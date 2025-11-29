"""Provider for fetching data from Yahoo Finance."""
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

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
                end=end_date + timedelta(days=1),
                progress=False,
            )
            if not yf_data.empty:
                close_prices = yf_data.get("Close")
                if close_prices is not None:
                    # yf.download with single ticker returns Series, multiple returns DataFrame
                    # We need to handle both
                    if len(yfinance_tickers_map) == 1:
                        yf_ticker = list(yfinance_tickers_map.keys())[0]
                        original_ticker = list(yfinance_tickers_map.values())[0]
                        # Series logic
                        for a_date, price in close_prices.dropna().items():
                            historical_data[original_ticker][
                                a_date.date()] = Decimal(str(price))
                    else:
                        for yf_ticker, original_ticker in yfinance_tickers_map.items():
                            if yf_ticker in close_prices:
                                for a_date, price in close_prices[yf_ticker].dropna().items(): # noqa: E501
                                    historical_data[original_ticker][
                                        a_date.date()] = Decimal(str(price))
        except (Exception, ValidationError) as e:
            print(f"WARNING: Error fetching historical data from yfinance: {e}")
            return {}

        if self.cache_client:
            fetched_tickers = set(historical_data.keys())
            for asset in assets_to_fetch:
                if asset["ticker_symbol"] not in fetched_tickers:
                    cache_key = f"asset_details_not_found:{asset['ticker_symbol'].upper()}" # noqa: E501
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
                    return {"name": info.get("shortName") or info.get("longName"), "asset_type": asset_type_map.get(info.get("quoteType"), "Stock"), "exchange": info.get("exchange"), "currency": info.get("currency", "INR")} # noqa: E501
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
        for yf_ticker_str in [f"{ticker_symbol}.NS", f"{ticker_symbol}.BO", ticker_symbol]: # noqa: E501
            temp_ticker = yf.Ticker(yf_ticker_str)
            if not temp_ticker.history(period="1d").empty:
                ticker_obj = temp_ticker
                break
        if ticker_obj:
            hist = ticker_obj.history(period="2d")
            if not hist.empty:
                return Decimal(str(hist["Close"].iloc[-1]))
        return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Yahoo Finance does not provide a direct search API. This is a no-op."""
        return []

    def get_exchange_rate(self, from_currency: str, to_currency: str, date_obj: date) -> Optional[Decimal]:
        ticker = f"{from_currency}{to_currency}=X"
        # Use get_historical_prices for single day
        result = self.get_historical_prices(
            [{"ticker_symbol": ticker, "exchange": None}],
            date_obj,
            date_obj
        )
        if result and ticker in result and date_obj in result[ticker]:
             return result[ticker][date_obj]

        # If today, fallback to get_price which uses history('2d') or similar
        if date_obj == date.today():
             return self.get_price(ticker)

        return None
