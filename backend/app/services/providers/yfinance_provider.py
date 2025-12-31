"""Provider for fetching data from Yahoo Finance."""
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf
from pydantic import ValidationError

from app.cache.base import CacheClient

from .base import FinancialDataProvider

CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours

logger = logging.getLogger(__name__)


class YFinanceProvider(FinancialDataProvider):
    def __init__(self, cache_client: Optional[CacheClient]):
        self.cache_client = cache_client

    def _get_yfinance_ticker(
        self, ticker_symbol: str, exchange: Optional[str]
    ) -> str:
        """Constructs the correct ticker for yfinance."""
        if str(exchange).upper() in ("NSE", "NSI"):
            return f"{ticker_symbol}.NS"
        if exchange == "BSE":
            return f"{ticker_symbol}.BO"
        return ticker_symbol

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        logger.debug(
            "YFinanceProvider: get_current_prices called for assets: "
            f"{[a.get('ticker_symbol') for a in assets]}"
        )
        prices_data: Dict[str, Dict[str, Decimal]] = {}
        tickers_to_fetch: List[Dict[str, Any]] = []

        if self.cache_client:
            for asset in assets:
                original_ticker = asset["ticker_symbol"]
                ticker = self._get_yfinance_ticker(
                    original_ticker, asset.get("exchange")
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

        yfinance_tickers_str = " ".join(
            [
                self._get_yfinance_ticker(a["ticker_symbol"], a["exchange"])
                for a in tickers_to_fetch
            ]
        )
        logger.debug(
            f"Fetching from yfinance API with tickers: '{yfinance_tickers_str}'"
        )

        try:
            yf_data = yf.Tickers(yfinance_tickers_str)
            for ticker_obj in yf_data.tickers.values():
                hist = ticker_obj.history(period="2d", auto_adjust=True)
                yf_symbol = ticker_obj.ticker
                original_ticker = yf_symbol.split(".")[0]

                if not hist.empty and len(hist) >= 2:
                    current_price = Decimal(str(hist["Close"].iloc[-1]))
                    logger.debug(
                        f"yfinance API SUCCESS for {yf_symbol}. Price: {current_price}"
                    )
                    previous_close = Decimal(str(hist["Close"].iloc[-2]))
                    prices_data[original_ticker] = {
                        "current_price": current_price,
                        "previous_close": previous_close,
                    }
                elif not hist.empty and len(hist) == 1:
                    current_price = Decimal(str(hist["Close"].iloc[-1]))
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
        Fetches sector, industry, country, and marketCap for a single ticker.
        Called on-demand when an asset's sector is NULL.
        Returns dict with keys: sector, industry, country, market_cap
        """
        yf_ticker = self._get_yfinance_ticker(ticker_symbol, exchange)
        cache_key = f"enrichment:{yf_ticker}"

        # Check cache first
        if self.cache_client:
            cached = self.cache_client.get_json(cache_key)
            if cached:
                logger.debug(f"Enrichment cache HIT for {yf_ticker}")
                return cached

        try:
            ticker_obj = yf.Ticker(yf_ticker)
            info = ticker_obj.info
            if info:
                enrichment_data = {
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "country": info.get("country"),
                    "market_cap": info.get("marketCap"),
                }
                # Cache for 24 hours
                if self.cache_client:
                    self.cache_client.set_json(
                        cache_key, enrichment_data, expire=CACHE_TTL_HISTORICAL_PRICE
                    )
                logger.debug(
                    f"Enrichment fetched for {ticker_symbol}: "
                    f"sector={info.get('sector')}"
                )
                return enrichment_data
        except Exception as e:
            logger.warning(f"Error fetching enrichment for {ticker_symbol}: {e}")

        return None


    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
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
            yf_data = yf.download(
                yfinance_tickers_str,
                start=start_date,
                end=end_date + timedelta(days=1),  # end date is exclusive
                progress=False,
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
                                    a_date.date()] = Decimal(str(price))
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
                                            a_date.date()] = Decimal(str(price))
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

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        if self.cache_client:
            cache_key = f"asset_details_not_found:{ticker_symbol.upper()}"
            if self.cache_client.get_json(cache_key):
                return None

        ticker_obj = None
        for yf_ticker_str in [
            f"{ticker_symbol}.NS", f"{ticker_symbol}.BO", ticker_symbol
        ]:
            try:
                temp_ticker = yf.Ticker(yf_ticker_str)
                if not temp_ticker.history(period="1d").empty:
                    ticker_obj = temp_ticker
                    break
            except Exception:
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
                    return {
                        "name": info.get("shortName") or info.get("longName"),
                        "asset_type": asset_type_map.get(
                            info.get("quoteType"), "Stock"
                        ),
                        "exchange": info.get("exchange"),
                        "currency": info.get("currency", "INR"),
                    }
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
        for yf_ticker_str in [
            f"{ticker_symbol}.NS", f"{ticker_symbol}.BO", ticker_symbol
        ]:
            try:
                temp_ticker = yf.Ticker(yf_ticker_str)
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
                return Decimal(str(hist["Close"].iloc[-1]))
        return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Yahoo Finance does not provide a direct search API. This is a no-op."""
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
