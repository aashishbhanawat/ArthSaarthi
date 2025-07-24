import json
from collections import defaultdict
from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional

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
            self.redis_client: Optional[redis.Redis] = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            print("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            print(f"WARNING: Could not connect to Redis: {e}. Caching will be disabled.")
            self.redis_client = None

    def get_asset_price(self, ticker: str) -> Decimal:
        """
        Mocked function to get the current price of an asset.
        In a real implementation, this would call an external API.
        """
        # This is a mock implementation for demonstration purposes
        mock_prices = {
            "AAPL": Decimal("150.00"),
            "GOOGL": Decimal("2800.00"),
            "BTC": Decimal("45000.00"),
            "TSLA": Decimal("250.00"),
            "NVDA": Decimal("450.00"),
        }
        return mock_prices.get(ticker.upper(), Decimal("0.0"))

    def get_asset_details(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Mocked function to get details of an asset.
        In a real implementation, this would call an external API.
        """
        # This is a mock implementation for demonstration purposes
        mock_details = {
            "AAPL": {
                "name": "Apple Inc.",
                "asset_type": "STOCK",
                "currency": "USD",
                "exchange": "NASDAQ",
                "isin": "US0378331005",
            },
            "GOOGL": {
                "name": "Alphabet Inc.",
                "asset_type": "STOCK",
                "currency": "USD",
                "exchange": "NASDAQ",
                "isin": "US02079K3059",
            },
        }
        return mock_details.get(ticker.upper())

    def _get_yfinance_ticker(self, ticker_symbol: str, exchange: str) -> str:
        """Constructs the correct ticker for yfinance."""
        if exchange == "NSE":
            return f"{ticker_symbol}.NS"
        if exchange == "BSE":
            return f"{ticker_symbol}.BO"
        return ticker_symbol

    def get_current_prices(self, assets: List[Dict[str, Any]]) -> Dict[str, Decimal]:
        prices = {}
        tickers_to_fetch = []

        if self.redis_client:
            for asset in assets:
                ticker = asset["ticker_symbol"]
                cache_key = f"price:{ticker}"
                cached_price = self.redis_client.get(cache_key)
                if cached_price:
                    prices[ticker] = Decimal(cached_price)
                else:
                    tickers_to_fetch.append(asset)
        else:
            tickers_to_fetch = assets

        if not tickers_to_fetch:
            return prices

        yfinance_tickers_str = " ".join(
            [self._get_yfinance_ticker(a["ticker_symbol"], a["exchange"]) for a in tickers_to_fetch]
        )
        
        try:
            yf_data = yf.Tickers(yfinance_tickers_str)
            for ticker_obj in yf_data.tickers.values():
                info = ticker_obj.info
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                if price and info.get("symbol"):
                    # yfinance symbol can be like 'TCS.NS', we want to map back to 'TCS'
                    original_ticker = info.get("symbol").split('.')[0]
                    prices[original_ticker] = Decimal(str(price))
        except (Exception, ValidationError) as e:
            print(f"WARNING: Error fetching batch data from yfinance: {e}")

        if self.redis_client:
            for ticker, price in prices.items():
                if any(t['ticker_symbol'] == ticker for t in tickers_to_fetch):
                    self.redis_client.set(f"price:{ticker}", str(price), ex=CACHE_TTL_CURRENT_PRICE)

        return prices

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        historical_data = defaultdict(dict)
        yfinance_tickers_map = {
            self._get_yfinance_ticker(a["ticker_symbol"], a["exchange"]): a["ticker_symbol"]
            for a in assets
        }
        yfinance_tickers_str = " ".join(yfinance_tickers_map.keys())

        cache_key = f"history:{yfinance_tickers_str}:{start_date.isoformat()}:{end_date.isoformat()}"

        if self.redis_client:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                deserialized_data = json.loads(cached_data)
                for ticker, date_prices in deserialized_data.items():
                    for date_str, price_str in date_prices.items():
                        historical_data[ticker][datetime.fromisoformat(date_str).date()] = Decimal(price_str)
                return historical_data

        try:
            # yf.download end date is exclusive, so add one day
            yf_data = yf.download(yfinance_tickers_str, start=start_date, end=end_date + timedelta(days=1), progress=False)
            if yf_data.empty:
                return {}

            close_prices = yf_data.get('Close')
            if close_prices is None:
                return {}

            for yf_ticker, original_ticker in yfinance_tickers_map.items():
                if yf_ticker in close_prices:
                    for a_date, price in close_prices[yf_ticker].dropna().items():
                        historical_data[original_ticker][a_date.date()] = Decimal(str(price))

        except (Exception, ValidationError) as e:
            print(f"WARNING: Error fetching historical data from yfinance: {e}")
            return {}

        if self.redis_client:
            serializable_data = {}
            for ticker, date_prices in historical_data.items():
                serializable_data[ticker] = {
                    dt.isoformat(): str(price) for dt, price in date_prices.items()
                }
            self.redis_client.set(cache_key, json.dumps(serializable_data), ex=CACHE_TTL_HISTORICAL_PRICE)

        return historical_data


# Create a singleton instance to be used throughout the application
financial_data_service = FinancialDataService(redis_url=settings.REDIS_URL)