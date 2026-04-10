"""Provider for fetching data from Yahoo Finance."""
import logging
import time
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import yfinance as yf

from pydantic import ValidationError

from app.cache.base import CacheClient
from app.core.config import settings

from .base import FinancialDataProvider

import threading

CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours

logger = logging.getLogger(__name__)

# Global lock to serialize all Yahoo Finance HTTP requests.
# This prevents burst 429 errors when multiple threads request prices simultaneously.
_YFINANCE_LOCK = threading.Lock()


class YFinanceProvider(FinancialDataProvider):
    # Enforce singleton so all threads share one session and cache
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self, cache_client: Optional[CacheClient]):
        # Singleton guard: only initialize once
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.cache_client = cache_client
        
        from pathlib import Path
        self._last_429_time: float = 0
        self._cooldown_period: float = 60  # 1 minute cooldown after 429
        
        # In-process enrichment cache: serves as a fast fallback when Redis is
        # unavailable (e.g., Android). Prevents concurrent threads from all
        # independently querying Yahoo Finance for the same ticker info,
        # which is the root cause of 429 burst errors on Android.
        # Key: yf_ticker, Value: (data_dict, expiry_timestamp)
        self._enrichment_cache: dict = {}
        self._enrichment_cache_lock = threading.Lock()
        
        # We no longer use requests-cache session with yfinance because it's 
        # incompatible with yfinance's modern scraping logic (curl_cffi).
        # We rely on _YFINANCE_LOCK and self.cache_client for performance.
        
        # Conditionally apply User-Agent spoofing.
        # Diagnostic results (2026-04-10) confirmed that on Android, Yahoo 
        # Finance blocks default Python User-Agents due to TLS fingerprinting,
        # but allows Chrome fingerprints even from BoringSSL.
        # On Server/Desktop, curl_cffi is often available and handled better 
        # by yfinance internally. We only pass a session on Android to bypass
        # the 429 block.
        self.session = None
        if settings.DEPLOYMENT_MODE == "android":
            self.session = requests.Session()
            # Deep Browser Spoof: Use a full set of modern browser headers to 
            # mimic a standard Chrome navigation. This is more resilient than 
            # just the User-Agent.
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "DNT": "1",
                "Cache-Control": "max-age=0",
            })
            
            # Global Spoof: Intercept yfinance's internal User-Agent logic.
            # Some versions of yfinance may ignore the session's headers or 
            # overwrite them. We force it at the source.
            try:
                import yfinance.utils as yf_utils
                yf_utils.get_user_agent = lambda: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                logger.info("YFinanceProvider: Globally spoofed yfinance User-Agent.")
            except Exception as e:
                logger.warning(f"YFinanceProvider: Failed to globally spoof yfinance UA: {e}")

            logger.info("YFinanceProvider: Using Deep Chrome Spoofing for Android.")
        else:
            logger.info(f"YFinanceProvider: Let yf handle sessions for {settings.DEPLOYMENT_MODE} mode.")

    def _to_safe_decimal(self, value: Any) -> Decimal:
        """
        Safely convert a value (often from yfinance) to a Decimal.
        Handles NaN and Infinity which cause Pydantic v1 (Android) to crash.
        """
        try:
            if value is None:
                return Decimal("0")
            f_val = float(value)
            if not math.isfinite(f_val):
                return Decimal("0")
            # Using str(f_val) to maintain precision where possible
            return Decimal(str(f_val))
        except (ValueError, TypeError, Exception):
            return Decimal("0")

    def _is_cooling_down(self) -> bool:
        if self._last_429_time == 0:
            return False
        return (time.time() - self._last_429_time) < self._cooldown_period

    def close(self):
        """No-op. Session is managed by yfinance internally."""
        pass

    def _fetch_history_with_retry(self, ticker_obj, **kwargs) -> pd.DataFrame:
        kwargs.setdefault("auto_adjust", False)
        # Session already passed to ticker_obj during initialization
        df = ticker_obj.history(**kwargs)
        if df is None or df.empty:
            raise ValueError(f"yfinance history returned empty data for {ticker_obj.ticker}")
        return df

    def _fetch_download_with_retry(self, tickers_str, start_date, end_date) -> pd.DataFrame:
        if hasattr(yf, "shared"):
            yf.shared._ERRORS = {}
        df = yf.download(
            tickers_str,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=False,
            session=self.session
        )
        if hasattr(yf, "shared") and getattr(yf.shared, "_ERRORS", {}):
            errors = yf.shared._ERRORS
            if any("Rate limited" in str(e) or "Too Many Requests" in str(e) for e in errors.values()):
                raise ValueError(f"YFinance Rate Limit hit: {errors}")
        if df is None or df.empty:
            raise ValueError(f"yfinance download returned empty data for {tickers_str}")
        return df

    def _fetch_info_with_retry(self, ticker_obj) -> dict:
        return ticker_obj.info

    def _get_yfinance_ticker(
        self, ticker_symbol: str, exchange: Optional[str]
    ) -> str:
        """Constructs the correct ticker for yfinance."""
        # Don't add suffix if already present
        upper_ticker = ticker_symbol.upper()
        if upper_ticker.endswith('.NS') or upper_ticker.endswith('.BO'):
            return ticker_symbol

        if str(exchange).upper() in ("NSE", "NSI"):
            return f"{ticker_symbol}.NS"
        if exchange == "BSE":
            return f"{ticker_symbol}.BO"
        return ticker_symbol

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        if self._is_cooling_down():
            logger.warning("YFinance: Circuit breaker active (cooling down after 429)")
            return {}
            
        logger.debug(
            f"get_current_prices: {len(assets)} assets - "
            f"{[(a.get('ticker_symbol'), a.get('exchange')) for a in assets]}"
        )
        prices_data: Dict[str, Dict[str, Decimal]] = {}
        tickers_to_fetch: List[Dict[str, Any]] = []

        if self.cache_client:
            for asset in assets:
                original_ticker = asset["ticker_symbol"]
                ticker = self._get_yfinance_ticker(
                    original_ticker, asset.get("exchange")
                )
                logger.debug(
                    f"Ticker transform: {original_ticker} "
                    f"(exchange={asset.get('exchange')}) -> {ticker}"
                )
                cache_key = (
                    f"price_details:{ticker}"
                )  # Use the yfinance-specific ticker for cache key
                not_found_cache_key = f"asset_details_not_found:{ticker.upper()}"

                cached_data = self.cache_client.get_json(cache_key)
                if cached_data:
                    logger.debug(f"Cache HIT for {ticker}. Data: {cached_data}")
                    prices_data[original_ticker] = {
                        "current_price": Decimal(cached_data["current_price"]),
                        "previous_close": Decimal(cached_data["previous_close"]),
                    }
                    continue

                if self.cache_client.get_json(not_found_cache_key):
                    # Re-implement negative caching, but only to prevent spamming the
                    # API during a short user session. If an asset was not found, we
                    # try again after 15 minutes, not block it for 24 hours.
                    logger.debug(
                        f"Negative cache HIT for {ticker}. Skipping network fetch for"
                        " now."
                    )
                    # Do not add to tickers_to_fetch, but don't add to
                    # prices_data yet either.
                    pass
                else:
                    tickers_to_fetch.append(asset)
                    logger.debug(f"Cache MISS for {ticker}. Will fetch from network.")

        else:
            tickers_to_fetch = assets

        if not tickers_to_fetch:
            return prices_data

        # Build a reverse map: yf_ticker -> original DB ticker_symbol
        # e.g. {"NTPC.NS": "NTPC.NS", "TCS.NS": "TCS"} allows correct attribution
        # of fetched prices back to the exact ticker stored in the database.
        yf_to_original: Dict[str, str] = {
            self._get_yfinance_ticker(
                a["ticker_symbol"], a["exchange"]
            ): a["ticker_symbol"]
            for a in tickers_to_fetch
        }

        yfinance_tickers_str = " ".join(yf_to_original.keys())
        logger.debug(f"yfinance batch request: '{yfinance_tickers_str}'")

        try:
            # Acquire lock to serialize Yahoo requests across all threads.
            # This prevents the burst-429 issue when multiple portfolio
            # calculations are triggered concurrently.
            with _YFINANCE_LOCK:
                logger.debug(f"[LOCK] Acquired for tickers: {yfinance_tickers_str}")
                yf_data = yf.Tickers(yfinance_tickers_str, session=self.session)
                raw_results = {}
                for ticker_obj in yf_data.tickers.values():
                    hist = self._fetch_history_with_retry(ticker_obj, period="2d")
                    raw_results[ticker_obj.ticker] = hist

            for yf_symbol, hist in raw_results.items():
                # Use reverse map; fallback to splitting suffix for plain tickers
                original_ticker = yf_to_original.get(
                    yf_symbol, yf_symbol.split(".")[0]
                )
                logger.debug(
                    f"Processing ticker: request={yf_symbol}, "
                    f"mapped_to={original_ticker}, has_data={not hist.empty}"
                )

                if not hist.empty and len(hist) >= 2:
                    current_price = self._to_safe_decimal(hist["Close"].iloc[-1])
                    logger.debug(
                        f"Price fetched: {original_ticker}={current_price}"
                    )
                    previous_close = self._to_safe_decimal(hist["Close"].iloc[-2])
                    prices_data[original_ticker] = {
                        "current_price": current_price,
                        "previous_close": previous_close,
                    }
                elif not hist.empty and len(hist) == 1:
                    current_price = self._to_safe_decimal(hist["Close"].iloc[-1])
                    logger.debug(
                        f"yfinance API SUCCESS for {yf_symbol} (1 day data). Price: "
                        f"{current_price}"
                    )
                    prices_data[original_ticker] = {
                        "current_price": current_price,
                        "previous_close": current_price,
                    }
                else:
                    logger.warning(
                        f"yfinance API returned empty history for {yf_symbol}"
                    )
        except (Exception, ValidationError) as e:
            if "429" in str(e) or "Rate limit" in str(e):
                self._last_429_time = time.time()
            logger.error(f"WARNING: Error fetching batch data from yfinance: {e}")

        if self.cache_client:
            fetched_tickers = set(prices_data.keys())
            for asset_to_check in tickers_to_fetch:
                original_ticker = asset_to_check["ticker_symbol"]
                if original_ticker not in fetched_tickers:
                    yf_ticker_for_cache = self._get_yfinance_ticker(
                        original_ticker, asset_to_check.get("exchange")
                    )
                    not_found_cache_key = (
                        f"asset_details_not_found:{yf_ticker_for_cache.upper()}"
                    )
                    logger.debug(f"Setting 'not_found' cache for {yf_ticker_for_cache}")
                    self.cache_client.set_json(
                        not_found_cache_key,
                        {"not_found": True},
                        expire=CACHE_TTL_CURRENT_PRICE,  # Use a short TTL (15 mins)
                    )
            for ticker, data in prices_data.items():
                if any(t["ticker_symbol"] == ticker for t in tickers_to_fetch):
                    serializable_data = {
                        "current_price": str(data["current_price"]),
                        "previous_close": str(data["previous_close"]),
                    }
                    yf_ticker_for_cache = self._get_yfinance_ticker(ticker, any(
                        t["exchange"]
                        for t in tickers_to_fetch
                        if t["ticker_symbol"] == ticker
                    ))
                    self.cache_client.set_json(
                        f"price_details:{yf_ticker_for_cache}",
                        serializable_data,
                        expire=CACHE_TTL_CURRENT_PRICE,
                    )

        logger.debug(f"YFinanceProvider: returning prices for: {prices_data.keys()}")
        return prices_data

    def get_enrichment_data(
        self, ticker_symbol: str, exchange: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches sector, industry, country, marketCap, P/E, P/B for a single ticker.
        Called on-demand when an asset's sector is NULL.
        Returns dict with keys: sector, industry, country, market_cap,
                                trailing_pe, price_to_book, investment_style
        """
        yf_ticker = self._get_yfinance_ticker(ticker_symbol, exchange)
        cache_key = f"enrichment:{yf_ticker}"

        # 1. Check in-process memory cache first (works on Android without Redis)
        with self._enrichment_cache_lock:
            mem_cached = self._enrichment_cache.get(yf_ticker)
            if mem_cached:
                data, expiry = mem_cached
                if time.time() < expiry:
                    logger.debug(f"Enrichment in-process cache HIT for {yf_ticker}")
                    return data
                else:
                    del self._enrichment_cache[yf_ticker]

        # 2. Check Redis/disk cache
        if self.cache_client:
            cached = self.cache_client.get_json(cache_key)
            if cached:
                logger.debug(f"Enrichment Redis cache HIT for {yf_ticker}")
                return cached

        try:
            with _YFINANCE_LOCK:
                # Double-check both caches inside lock to avoid redundant network calls 
                # if another thread just finished fetching this ticker.
                with self._enrichment_cache_lock:
                    mem_cached = self._enrichment_cache.get(yf_ticker)
                    if mem_cached:
                        data, expiry = mem_cached
                        if time.time() < expiry:
                            return data

                if self.cache_client:
                    cached = self.cache_client.get_json(cache_key)
                    if cached:
                        return cached

                ticker_obj = yf.Ticker(yf_ticker, session=self.session)
                info = self._fetch_info_with_retry(ticker_obj)
                if info:
                    trailing_pe = info.get("trailingPE")
                    price_to_book = info.get("priceToBook")

                    # Classify investment style based on P/E and P/B
                    investment_style = self._classify_investment_style(
                        trailing_pe, price_to_book
                    )

                    enrichment_data = {
                        "sector": info.get("sector"),
                        "industry": info.get("industry"),
                        "country": info.get("country"),
                        "market_cap": info.get("marketCap"),
                        "trailing_pe": trailing_pe,
                        "price_to_book": price_to_book,
                        "investment_style": investment_style,
                    }
                    # Cache in Redis/disk (24 hours)
                    if self.cache_client:
                        self.cache_client.set_json(
                            cache_key, enrichment_data, expire=CACHE_TTL_HISTORICAL_PRICE
                        )
                    # Cache in-process (1 hour — shorter to avoid stale data on long runs)
                    with self._enrichment_cache_lock:
                        self._enrichment_cache[yf_ticker] = (
                            enrichment_data, time.time() + 3600
                        )
                    logger.debug(
                        f"Enrichment fetched for {ticker_symbol}: "
                        f"sector={info.get('sector')}, style={investment_style}"
                    )
                    return enrichment_data
        except Exception as e:
            logger.warning(f"Error fetching enrichment for {ticker_symbol}: {e}")
            if "429" in str(e) or "Rate limited" in str(e):
                self._last_429_time = time.time()

        return None

    def _classify_investment_style(
        self, trailing_pe: Optional[float], price_to_book: Optional[float]
    ) -> str:
        """
        Classifies investment style based on P/E and P/B ratios.

        Classification thresholds (based on typical market benchmarks):
        - Value: P/E < 15 AND P/B < 1.5
        - Growth: P/E > 25 OR P/B > 3.0
        - Blend: Everything else (moderate ratios)

        Returns: 'Value', 'Growth', or 'Blend'
        """
        if trailing_pe is None and price_to_book is None:
            return "Unknown"

        # Use available metrics
        pe = trailing_pe if trailing_pe and trailing_pe > 0 else None
        pb = price_to_book if price_to_book and price_to_book > 0 else None

        # Value criteria: Low P/E AND Low P/B
        is_value_pe = pe is not None and pe < 15
        is_value_pb = pb is not None and pb < 1.5

        # Growth criteria: High P/E OR High P/B
        is_growth_pe = pe is not None and pe > 25
        is_growth_pb = pb is not None and pb > 3.0

        # Classification logic
        if is_value_pe and is_value_pb:
            return "Value"
        elif is_growth_pe or is_growth_pb:
            return "Growth"
        elif pe is not None or pb is not None:
            return "Blend"
        else:
            return "Unknown"



    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        if self._is_cooling_down():
            logger.warning("YFinance: Circuit breaker active (cooling down after 429)")
            return {}
            
        historical_data: Dict[str, Dict[date, Decimal]] = defaultdict(dict)
        assets_to_fetch = []
        if self.cache_client:
            for asset in assets:
                not_found_cache_key = (
                    f"asset_details_not_found:{asset['ticker_symbol'].upper()}"
                )
                if not self.cache_client.get_json(not_found_cache_key):
                    assets_to_fetch.append(asset)
        else:
            assets_to_fetch = assets

        yfinance_tickers_map = {
            self._get_yfinance_ticker(a["ticker_symbol"], a["exchange"]): a[
                "ticker_symbol"
            ]
            for a in assets_to_fetch
        }
        yfinance_tickers_str = " ".join(yfinance_tickers_map.keys())
        cache_key = (
            f"history:{yfinance_tickers_str}:{start_date.isoformat()}:{end_date.isoformat()}"
        )

        if self.cache_client:
            cached_data = self.cache_client.get_json(cache_key)
            if cached_data:
                for ticker, date_prices in cached_data.items():
                    for date_str, price_str in date_prices.items():
                        historical_data[ticker][
                            datetime.fromisoformat(date_str).date()
                        ] = Decimal(price_str)
                return historical_data

        try:
            with _YFINANCE_LOCK:
                yf_data = self._fetch_download_with_retry(
                    yfinance_tickers_str,
                    start_date,
                    end_date + timedelta(days=1)
                )
            if not yf_data.empty:
                close_prices = yf_data.get("Close")
                if close_prices is not None:
                    # yf.download with a single ticker returns a Series for 'Close'.
                    # With multiple tickers, it returns a DataFrame.
                    if isinstance(close_prices, pd.Series):
                        original_ticker = list(yfinance_tickers_map.values())[0]
                        for a_date, price in close_prices.dropna().items():
                            try:
                                historical_data[original_ticker][
                                    a_date.date()] = self._to_safe_decimal(price)
                            except Exception:
                                logger.error(
                                    "Failed to convert price for %s on %s. "
                                    "Price: '%s', Type: %s",
                                    original_ticker,
                                    a_date.date(),
                                    price,
                                    type(price),
                                )
                    # Handle DataFrame for multiple tickers
                    else:
                        for yf_ticker, original_ticker in yfinance_tickers_map.items():
                            if yf_ticker in close_prices:
                                for a_date, price in close_prices[
                                    yf_ticker
                                ].dropna().items():
                                    try:
                                        historical_data[original_ticker][
                                            a_date.date()] = self._to_safe_decimal(price)
                                    except Exception:
                                        logger.error(
                                            "Failed to convert price for %s on %s. "
                                            "Price: '%s', Type: %s",
                                            original_ticker,
                                            a_date.date(),
                                            price,
                                            type(price),
                                        )

        except (Exception, ValidationError) as e:
            print(f"WARNING: Error fetching historical data from yfinance: {e}")
            return {}

        if self.cache_client:
            fetched_tickers = set(historical_data.keys())
            for asset in assets_to_fetch:
                if asset["ticker_symbol"] not in fetched_tickers:
                    cache_key = (
                        f"asset_details_not_found:{asset['ticker_symbol'].upper()}"
                    )
                    self.cache_client.set_json(
                        cache_key,
                        {"not_found": True},
                        expire=CACHE_TTL_HISTORICAL_PRICE,
                    )
            serializable_data = {
                t: {dt.isoformat(): str(price) for dt, price in dp.items()}
                for t, dp in historical_data.items()
            }
            self.cache_client.set_json(
                cache_key, serializable_data, expire=CACHE_TTL_HISTORICAL_PRICE
            )

        return historical_data

    def get_index_history(
        self, ticker_symbol: str, start_date: date, end_date: date
    ) -> Dict[str, float]:
        """
        Fetches historical closing prices for an index (e.g., ^NSEI, ^BSESN).
        Returns a dict of {date_str: close_price}.
        """
        yf_ticker = ticker_symbol  # Index tickers are already in yfinance format
        cache_key = (
            f"index_history:{yf_ticker}:{start_date.isoformat()}:{end_date.isoformat()}"
        )

        if self.cache_client:
            cached = self.cache_client.get_json(cache_key)
            if cached:
                logger.debug(f"Index history cache HIT for {yf_ticker}")
                return cached

        try:
            logger.info(
                f"Fetching index history for {yf_ticker} "
                f"from {start_date} to {end_date}"
            )
            ticker_obj = yf.Ticker(yf_ticker, session=self.session)
            # Fetch data with slight buffer
            hist = self._fetch_history_with_retry(
                ticker_obj, start=start_date, end=end_date + timedelta(days=1)
            )

            if hist.empty:
                logger.warning(f"No history found for index {yf_ticker}")
                return {}

            # Convert to dict {YYYY-MM-DD: price}
            history_dict = {}
            for index, row in hist.iterrows():
                date_str = index.date().isoformat()
                history_dict[date_str] = float(row["Close"])

            if self.cache_client:
                # Cache for 24 hours
                self.cache_client.set_json(
                    cache_key, history_dict, expire=CACHE_TTL_HISTORICAL_PRICE
                )

            return history_dict

        except Exception as e:
            logger.error(f"Error fetching index history for {yf_ticker}: {e}")
            return {}

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        if self.cache_client:
            cache_key = f"asset_details_not_found:{ticker_symbol.upper()}"
            if self.cache_client.get_json(cache_key):
                return None

        logger.debug(f"get_asset_details: Looking up {ticker_symbol}")
        ticker_obj = None

        upper_ticker = ticker_symbol.upper()
        if upper_ticker.endswith('.NS') or upper_ticker.endswith('.BO'):
            variants = [ticker_symbol]
        else:
            variants = [f"{ticker_symbol}.NS", f"{ticker_symbol}.BO", ticker_symbol]

        for yf_ticker_str in variants:
            try:
                logger.debug(f"Trying ticker variant: {yf_ticker_str}")
                temp_ticker = yf.Ticker(yf_ticker_str, session=self.session)
                if not temp_ticker.history(period="1d").empty:
                    logger.debug(f"Found data with variant: {yf_ticker_str}")
                    ticker_obj = temp_ticker
                    break
            except Exception as e:
                logger.debug(f"Ticker variant {yf_ticker_str} failed: {e}")
                continue

        if ticker_obj:
            try:
                info = ticker_obj.info
                if info and info.get("shortName"):
                    asset_type_map = {
                        "EQUITY": "Stock",
                        "MUTUALFUND": "Mutual Fund",
                        "ETF": "ETF",
                        "CRYPTOCURRENCY": "Crypto",
                    }
                    result = {
                        "name": info.get("shortName") or info.get("longName"),
                        "asset_type": asset_type_map.get(
                            info.get("quoteType"), "Stock"
                        ),
                        "exchange": info.get("exchange"),
                        "currency": info.get("currency", "INR"),
                    }
                    logger.debug(f"Asset details for {ticker_symbol}: {result}")
                    return result
            except (IndexError, KeyError):
                pass

        if self.cache_client:
            cache_key = f"asset_details_not_found:{ticker_symbol.upper()}"
            self.cache_client.set_json(
                cache_key, {"not_found": True}, expire=CACHE_TTL_HISTORICAL_PRICE
            )
        return None

    def get_price(self, ticker_symbol: str) -> Optional[Decimal]:
        ticker_obj = None

        upper_ticker = ticker_symbol.upper()
        if upper_ticker.endswith('.NS') or upper_ticker.endswith('.BO'):
            variants = [ticker_symbol]
        else:
            variants = [f"{ticker_symbol}.NS", f"{ticker_symbol}.BO", ticker_symbol]

        for yf_ticker_str in variants:
            try:
                temp_ticker = yf.Ticker(yf_ticker_str, session=self.session)
                if not temp_ticker.history(period="1d").empty:
                    ticker_obj = temp_ticker
                    break
            except (ValueError, Exception) as e:
                # yfinance raises ValueError for invalid ISIN-formatted symbols
                # (e.g., bond ISINs like "IN0020210129" that start with country codes)
                logger.debug(f"yfinance rejected ticker {yf_ticker_str}: {e}")
                continue
        if ticker_obj:
            hist = ticker_obj.history(period="2d")
            if not hist.empty:
                return self._to_safe_decimal(hist["Close"].iloc[-1])
        return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Yahoo Finance for matching tickers by name, ticker, or ISIN.
        Returns a list of matching assets with their details.
        """
        if self._is_cooling_down():
            return []

        try:
            with _YFINANCE_LOCK:
                # yfinance provides a Search class for querying Yahoo Finance
                search_obj = yf.Search(query, session=self.session)
                quotes = getattr(search_obj, 'quotes', [])

            results = []
            for quote in quotes[:10]:  # Limit to top 10 results
                # Map Yahoo's quoteType to our asset types
                quote_type = quote.get("quoteType", "").upper()
                asset_type = "STOCK"  # Default
                if quote_type == "ETF":
                    asset_type = "ETF"
                elif quote_type == "MUTUALFUND":
                    asset_type = "Mutual Fund"
                elif quote_type in ("EQUITY", "STOCK"):
                    asset_type = "STOCK"

                results.append({
                    "ticker_symbol": quote.get("symbol"),
                    "name": quote.get("shortname") or quote.get("longname"),
                    "exchange": quote.get("exchange"),
                    "asset_type": asset_type,
                    "currency": quote.get("currency"),
                })

            logger.debug(
                f"Yahoo search for '{query}': "
                f"{[(r['ticker_symbol'], r['name']) for r in results]}"
            )
            return results
        except Exception as e:
            logger.warning(f"Yahoo search failed for '{query}': {e}")
            return []

    def get_exchange_rate(
        self, from_currency: str, to_currency: str, date_obj: date
    ) -> Optional[Decimal]:
        """
        Fetches the exchange rate for a given date. If the rate for the exact
        date is not available (e.g., holiday/weekend), it finds the most
        recent previous day's rate within a 7-day window.
        """
        # 1. Input validation: Prevent invalid dates from reaching yfinance
        if date_obj.year < 1900:
            logger.error(
                "Received invalid year in date for FX rate lookup: %s", date_obj
            )
            return None

        ticker = f"{from_currency}{to_currency}=X"
        # Fetch a 7-day window to robustly handle weekends and holidays.
        # yfinance `end` is exclusive, so we add one day.
        start_date = date_obj - timedelta(days=7)
        end_date = date_obj + timedelta(days=1)

        result = self.get_historical_prices(
            [{"ticker_symbol": ticker, "exchange": None}], # type: ignore
            start_date,
            end_date
        )
        if result and ticker in result and result[ticker]:
            # Find the most recent available date up to and including the
            # requested date
            available_dates = sorted(
                [d for d in result[ticker].keys() if d <= date_obj], reverse=True
            )
            if available_dates:
                latest_available_date = available_dates[0]
                logger.info(
                    "Using FX rate from %s for requested date %s",
                    latest_available_date, date_obj
                )
                return result[ticker][latest_available_date]
        return None
