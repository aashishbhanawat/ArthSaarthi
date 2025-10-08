from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional


class FinancialDataProvider(ABC):
    @abstractmethod
    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        """Fetches current and previous day's close price for a list of assets."""
        pass

    @abstractmethod
    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        """Fetches historical prices for a list of assets over a date range."""
        pass

    @abstractmethod
    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """Fetches details for a single asset."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Searches for assets supported by the provider."""
        pass
