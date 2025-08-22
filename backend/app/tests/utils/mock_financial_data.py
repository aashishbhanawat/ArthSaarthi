from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional


class MockFinancialDataService:
    def get_current_prices(
        self, assets: List[Dict]
    ) -> Dict[str, Dict[str, Decimal]]:
        prices = {}
        for asset in assets:
            ticker = asset["ticker_symbol"]
            prices[ticker] = {
                "current_price": Decimal(f"{100.0 + len(ticker)}"),
                "previous_close": Decimal(f"{99.0 + len(ticker)}"),
            }
        return prices

    def get_historical_prices(
        self, assets: List[Dict], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        prices = defaultdict(dict)
        for asset in assets:
            ticker = asset["ticker_symbol"]
            current_day = start_date
            price = 100.0 + len(ticker)
            while current_day <= end_date:
                prices[ticker][current_day] = Decimal(f"{price}")
                price += (len(ticker) % 4) - 1.5  # fluctuate price
                current_day += timedelta(days=1)
        return prices

    def get_asset_details(
        self, ticker_symbol: str, exchange: Optional[str] = None
    ) -> Optional[Dict]:
        print(f"MockFinancialDataService: get_asset_details for {ticker_symbol}")
        mock_data = {
            "RELIANCE": {
                "name": "Reliance Industries",
                "asset_type": "STOCK",
                "currency": "INR",
                "exchange": "NSE",
            },
            "MSFT": {
                "name": "Microsoft Corporation",
                "asset_type": "STOCK",
                "currency": "USD",
                "exchange": "NASDAQ",
            },
            "GOOGL": {
                "name": "Alphabet Inc.",
                "asset_type": "STOCK",
                "currency": "USD",
                "exchange": "NASDAQ",
            },
            "AAPL": {
                "name": "Apple Inc.",
                "asset_type": "STOCK",
                "currency": "USD",
                "exchange": "NASDAQ",
            },
            "XIRRTEST": {
                "name": "XIRR Test Company",
                "asset_type": "Stock",
                "exchange": "TEST",
                "currency": "INR",
            },
            "NTPC": {
                "name": "NTPC Limited",
                "asset_type": "STOCK",
                "currency": "INR",
                "exchange": "NSE",
            },
            "SCI": {
                "name": "Shipping Corporation of India",
                "asset_type": "STOCK",
                "currency": "INR",
                "exchange": "NSE",
            },
            "TXN1": {
                "name": "Transaction Asset 1",
                "asset_type": "STOCK",
                "currency": "USD",
                "exchange": "NASDAQ",
            },
            "TXN2": {
                "name": "Transaction Asset 2",
                "asset_type": "STOCK",
                "currency": "USD",
                "exchange": "NASDAQ",
            },
        }
        details = mock_data.get(ticker_symbol)
        print(f"MockFinancialDataService: found details: {details}")
        return details
