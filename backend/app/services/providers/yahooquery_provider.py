"""Provider for fetching data from Yahoo Finance using yahooquery."""
import logging
import random
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
import requests_cache
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from yahooquery import Ticker
from pydantic import ValidationError
from app.cache.base import CacheClient
from app.core.config import settings
from .base import FinancialDataProvider

CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours

logger = logging.getLogger(__name__)

class YahooQueryProvider(FinancialDataProvider):
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    ]

    def __init__(self, cache_client: Optional[CacheClient]):
        self.cache_client = cache_client
        self.user_agent = random.choice(self.USER_AGENTS)
        self.session = self._get_session()
        self._last_429_time: float = 0
        self._cooldown_period: float = 60  # 1 minute cooldown after 429

    def _is_cooling_down(self) -> bool:
        if self._last_429_time == 0:
            return False
        return (time.time() - self._last_429_time) < self._cooldown_period

    def _get_session(self) -> Session:
        # Use CachedSession to store responses locally (SQLite)
        from pathlib import Path
        cache_path = str(Path(settings.DISK_CACHE_DIR) / "yahooquery_cache.sqlite")
        session = requests_cache.CachedSession(
            cache_path,
            backend='sqlite',
            expire_after=CACHE_TTL_HISTORICAL_PRICE,  # 24 hours
            allowable_codes=[200],
            stale_if_error=True
        )
        session.headers.update({"User-Agent": self.user_agent})
        # Add retry strategy for 429 and 5xx errors
        retries = Retry(
            total=3,
            backoff_factor=3,  # Exponential backoff: 3s, 9s, 27s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        return session

    def _get_ticker_session(self, symbols: Any) -> Ticker:
        # Randomized sleep to avoid burst requests (jitter)
        time.sleep(random.uniform(0.5, 2.0))
        return Ticker(symbols, session=self.session, region='IN', country='india')

    def _get_yahoo_ticker(
        self, ticker_symbol: str, exchange: Optional[str]
    ) -> str:
        """Constructs the correct ticker for Yahoo Finance."""
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
            logger.warning("YahooQuery: Circuit breaker active (cooling down after 429)")
            return {}
            
        logger.info(f"YahooQuery: Fetching current prices for {len(assets)} assets")
        prices_data: Dict[str, Dict[str, Decimal]] = {}
        tickers_to_fetch: List[Dict[str, Any]] = []

        if self.cache_client:
            for asset in assets:
                ticker = self._get_yahoo_ticker(asset["ticker_symbol"], asset.get("exchange"))
                cache_key = f"price_details:{ticker}"
                cached_data = self.cache_client.get_json(cache_key)
                if cached_data:
                    prices_data[asset["ticker_symbol"]] = {
                        "current_price": Decimal(cached_data["current_price"]),
                        "previous_close": Decimal(cached_data["previous_close"]),
                    }
                else:
                    tickers_to_fetch.append(asset)
        else:
            tickers_to_fetch = assets

        if not tickers_to_fetch:
            return prices_data

        yf_to_original = {
            self._get_yahoo_ticker(a["ticker_symbol"], a["exchange"]): a["ticker_symbol"]
            for a in tickers_to_fetch
        }
        
        symbols = list(yf_to_original.keys())
        try:
            t = self._get_ticker_session(symbols)
            # history(period='2d') returns a MultiIndex DataFrame (symbol, date)
            history = t.history(period="2d")
            
            if not history.empty:
                for yf_symbol, original_symbol in yf_to_original.items():
                    if yf_symbol in history.index.get_level_values(0):
                        symbol_history = history.loc[yf_symbol]
                        if len(symbol_history) >= 1:
                            current_price = Decimal(str(symbol_history["close"].iloc[-1]))
                            prev_close = current_price
                            if len(symbol_history) >= 2:
                                prev_close = Decimal(str(symbol_history["close"].iloc[-2]))
                            
                            prices_data[original_symbol] = {
                                "current_price": current_price,
                                "previous_close": prev_close,
                            }
                            
                            # Cache the result
                            if self.cache_client:
                                self.cache_client.set_json(
                                    f"price_details:{yf_symbol}",
                                    {
                                        "current_price": str(current_price),
                                        "previous_close": str(prev_close),
                                    },
                                    expire=CACHE_TTL_CURRENT_PRICE
                                )
        except Exception as e:
            logger.error(f"YahooQuery: Error fetching current prices: {e}")

        return prices_data

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        if self._is_cooling_down():
            logger.warning("YahooQuery: Circuit breaker active (cooling down after 429)")
            return {}
            
        logger.info(f"YahooQuery: Fetching historical prices for {len(assets)} assets")
        historical_data: Dict[str, Dict[date, Decimal]] = defaultdict(dict)
        yf_to_original = {
            self._get_yahoo_ticker(a["ticker_symbol"], a["exchange"]): a["ticker_symbol"]
            for a in assets
        }
        symbols = list(yf_to_original.keys())
        
        try:
            t = self._get_ticker_session(symbols)
            history = t.history(start=start_date, end=end_date + timedelta(days=1))
            
            if not history.empty:
                for yf_symbol, original_symbol in yf_to_original.items():
                    if yf_symbol in history.index.get_level_values(0):
                        symbol_history = history.loc[yf_symbol]
                        for a_date, row in symbol_history.iterrows():
                            # a_date is a Timestamp or date depending on pandas version/index
                            actual_date = a_date.date() if hasattr(a_date, 'date') else a_date
                            historical_data[original_symbol][actual_date] = Decimal(str(row["close"]))
        except Exception as e:
            logger.error(f"YahooQuery: Error fetching historical prices: {e}")

        return historical_data

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        if self._is_cooling_down():
            return None
        yf_ticker = self._get_yahoo_ticker(ticker_symbol, None)
        try:
            t = self._get_ticker_session(yf_ticker)
            # Fetch price and summaryProfile modules
            all_modules = t.all_modules
            if not isinstance(all_modules, dict):
                return None
                
            modules = all_modules.get(yf_ticker)
            if isinstance(modules, dict):
                price = modules.get('price', {})
                profile = modules.get('summaryProfile', {})
                
                asset_type_map = {
                    "EQUITY": "Stock",
                    "MUTUALFUND": "Mutual Fund",
                    "ETF": "ETF",
                    "CRYPTOCURRENCY": "Crypto",
                }
                
                return {
                    "name": price.get("shortName") or price.get("longName"),
                    "asset_type": asset_type_map.get(price.get("quoteType"), "Stock"),
                    "exchange": price.get("exchangeName"),
                    "currency": price.get("currency", "INR"),
                }
        except Exception as e:
            logger.debug(f"YahooQuery: Asset details lookup failed for {ticker_symbol}: {e}")
        return None

    def get_enrichment_data(
        self, ticker_symbol: str, exchange: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if self._is_cooling_down():
            return None
        yf_ticker = self._get_yahoo_ticker(ticker_symbol, exchange)
        try:
            t = self._get_ticker_session(yf_ticker)
            # assetProfile and summaryDetail contain the requested metrics
            all_modules = t.all_modules
            if not isinstance(all_modules, dict):
                return None
                
            modules = all_modules.get(yf_ticker)
            if isinstance(modules, dict):
                profile = modules.get('assetProfile', {})
                summary = modules.get('summaryDetail', {})
                
                trailing_pe = summary.get("trailingPE")
                price_to_book = summary.get("priceToBook")
                
                return {
                    "sector": profile.get("sector"),
                    "industry": profile.get("industry"),
                    "country": profile.get("country"),
                    "market_cap": summary.get("marketCap"),
                    "trailing_pe": trailing_pe,
                    "price_to_book": price_to_book,
                }
        except Exception as e:
            logger.warning(f"YahooQuery: Enrichment failed for {ticker_symbol}: {e}")
        return None

    def get_enrichment_data_batch(
        self, tickers: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Fetches enrichment data for multiple tickers in a single call."""
        if not tickers or self._is_cooling_down():
            return {}

        yf_to_original = {
            self._get_yahoo_ticker(a["ticker_symbol"], a.get("exchange")): a["ticker_symbol"]
            for a in tickers
        }
        symbols = list(yf_to_original.keys())
        
        enrichment_results = {}
        try:
            t = self._get_ticker_session(symbols)
            all_data = t.all_modules
            
            if isinstance(all_data, dict):
                for yf_symbol, original_symbol in yf_to_original.items():
                    data = all_data.get(yf_symbol)
                    if isinstance(data, dict):
                        profile = data.get('assetProfile', {})
                        summary = data.get('summaryDetail', {})
                        
                        enrichment_results[original_symbol] = {
                            "sector": profile.get("sector"),
                            "industry": profile.get("industry"),
                            "country": profile.get("country"),
                            "market_cap": summary.get("marketCap"),
                            "trailing_pe": summary.get("trailingPE"),
                            "price_to_book": summary.get("priceToBook"),
                        }
        except Exception as e:
            if "429" in str(e):
                self._last_429_time = time.time()
            logger.warning(f"YahooQuery: Batch enrichment failed: {e}")
            
        return enrichment_results

    def search(self, query: str) -> List[Dict[str, Any]]:
        try:
            from yahooquery import search
            search_results = search(query)
            quotes = search_results.get("quotes", [])
            
            results = []
            for quote in quotes[:10]:
                quote_type = quote.get("quoteType", "").upper()
                asset_type = "STOCK"
                if quote_type == "ETF":
                    asset_type = "ETF"
                elif quote_type == "MUTUALFUND":
                    asset_type = "Mutual Fund"
                
                results.append({
                    "ticker_symbol": quote.get("symbol"),
                    "name": quote.get("shortname") or quote.get("longname"),
                    "exchange": quote.get("exchange"),
                    "asset_type": asset_type,
                    "currency": quote.get("currency"),
                })
            return results
        except Exception as e:
            logger.warning(f"YahooQuery: Search failed for {query}: {e}")
        return []
