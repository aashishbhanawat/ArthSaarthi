import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import redis
import yfinance as yf
from pydantic import ValidationError

from app.core.config import settings

# Constants
CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours


class FinancialDataService:
    def __init__(self, redis_url: str):
        try:
            self.redis_client: Optional[redis.Redis] = redis.from_url(
                redis_url, decode_responses=True
            )
            self.redis_client.ping()
            print("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            print(
                f"WARNING: Could not connect to Redis: {e}. Caching will be disabled."
            )
            self.redis_client = None

    def _get_yfinance_ticker(self, ticker_symbol: str, exchange: Optional[str]) -> str:
        """Constructs the correct ticker for yfinance."""
        if exchange == "NSE":
            return f"{ticker_symbol}.NS"
        if exchange == "BSE":
            return f"{ticker_symbol}.BO"
        return ticker_symbol

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        prices_data = {}
        tickers_to_fetch = []

        # Handle mock data for E2E tests to ensure deterministic results
        non_mock_assets = []
        for asset in assets:
            if asset["ticker_symbol"] == "XIRRTEST":
                prices_data["XIRRTEST"] = {
                    "current_price": Decimal("130.00"),
                    "previous_close": Decimal("129.00"),
                }
            else:
                non_mock_assets.append(asset)
        # Continue with non-mocked assets
        assets = non_mock_assets

        if self.redis_client:
            for asset in assets:
                ticker = asset["ticker_symbol"]
                cache_key = f"price_details:{ticker}"
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    prices_data[ticker] = {
                        "current_price": Decimal(data["current_price"]),
                        "previous_close": Decimal(data["previous_close"]),
                    }
                else:
                    tickers_to_fetch.append(asset)
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

        try:
            yf_data = yf.Tickers(yfinance_tickers_str)
            for ticker_obj in yf_data.tickers.values():
                # Using history is more reliable for price data than .info
                hist = ticker_obj.history(period="2d", auto_adjust=True)

                # yfinance symbol can be like 'TCS.NS', we want to map back to 'TCS'
                yf_symbol = ticker_obj.ticker
                original_ticker = yf_symbol.split(".")[0]

                if not hist.empty and len(hist) >= 2:
                    current_price = Decimal(str(hist["Close"].iloc[-1]))
                    previous_close = Decimal(str(hist["Close"].iloc[-2]))
                    prices_data[original_ticker] = {
                        "current_price": current_price,
                        "previous_close": previous_close,
                    }
                elif not hist.empty and len(hist) == 1:
                    current_price = Decimal(str(hist["Close"].iloc[-1]))
                    prices_data[original_ticker] = {
                        "current_price": current_price,
                        "previous_close": current_price,  # Fallback
                    }
        except (Exception, ValidationError) as e:
            print(f"WARNING: Error fetching batch data from yfinance: {e}")

        if self.redis_client:
            for ticker, data in prices_data.items():
                if any(t["ticker_symbol"] == ticker for t in tickers_to_fetch):
                    serializable_data = {
                        "current_price": str(data["current_price"]),
                        "previous_close": str(data["previous_close"]),
                    }
                    self.redis_client.set(
                        f"price_details:{ticker}",
                        json.dumps(serializable_data),
                        ex=CACHE_TTL_CURRENT_PRICE,
                    )

        return prices_data

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        historical_data = defaultdict(dict)
        yfinance_tickers_map = {
            self._get_yfinance_ticker(a["ticker_symbol"], a["exchange"]): a[
                "ticker_symbol"
            ]
            for a in assets
        }
        yfinance_tickers_str = " ".join(yfinance_tickers_map.keys())

        cache_key = (
            f"history:{yfinance_tickers_str}:{start_date.isoformat()}:"
            f"{end_date.isoformat()}"
        )

        if self.redis_client:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                deserialized_data = json.loads(cached_data)
                for ticker, date_prices in deserialized_data.items():
                    for date_str, price_str in date_prices.items():
                        historical_data[ticker][
                            datetime.fromisoformat(date_str).date()
                        ] = Decimal(price_str)
                return historical_data

        try:
            # yf.download end date is exclusive, so add one day
            yf_data = yf.download(
                yfinance_tickers_str,
                start=start_date,
                end=end_date + timedelta(days=1),
                progress=False,
            )
            if yf_data.empty:
                return {}

            close_prices = yf_data.get("Close")
            if close_prices is None:
                return {}

            for yf_ticker, original_ticker in yfinance_tickers_map.items():
                if yf_ticker in close_prices:
                    for a_date, price in close_prices[yf_ticker].dropna().items():
                        historical_data[original_ticker][a_date.date()] = Decimal(
                            str(price)
                        )

        except (Exception, ValidationError) as e:
            print(f"WARNING: Error fetching historical data from yfinance: {e}")
            return {}

        if self.redis_client:
            serializable_data = {}
            for ticker, date_prices in historical_data.items():
                serializable_data[ticker] = {
                    dt.isoformat(): str(price) for dt, price in date_prices.items()
                }
            self.redis_client.set(
                cache_key, json.dumps(serializable_data), ex=CACHE_TTL_HISTORICAL_PRICE
            )

        return historical_data

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches details for a single asset from yfinance.
        Tries to find the asset on NSE, then BSE, then as-is.
        """
        # Handle mock data for E2E tests to ensure deterministic results
        if ticker_symbol == "XIRRTEST":
            return {
                "name": "XIRR Test Company",
                "asset_type": "Stock",
                "exchange": "TEST",
                "currency": "INR",
            }

        # Prioritize Indian exchanges
        potential_tickers = [
            f"{ticker_symbol}.NS",
            f"{ticker_symbol}.BO",
            ticker_symbol,
        ]
        for yf_ticker_str in potential_tickers:
            try:
                ticker_obj = yf.Ticker(yf_ticker_str)
                info = ticker_obj.info

                # Check for enough info to be considered valid
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
            except Exception:
                # yfinance often raises generic exceptions for invalid tickers
                continue
        return None


# Create a singleton instance to be used throughout the application
financial_data_service = FinancialDataService(redis_url=settings.REDIS_URL)
