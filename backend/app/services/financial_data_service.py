from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.cache.base import CacheClient
from app.core.config import settings

from .providers.amfi_provider import AmfiIndiaProvider  # type: ignore
from .providers.nse_bhavcopy_provider import NseBhavcopyProvider
from .providers.yfinance_provider import YFinanceProvider  # type: ignore

CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours


class FinancialDataService:
    def __init__(self, cache_client: Optional[CacheClient]):
        self.yfinance_provider = YFinanceProvider(cache_client)
        self.amfi_provider = AmfiIndiaProvider(cache_client)
        self.nse_provider = NseBhavcopyProvider(cache_client)

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Fetches current prices by delegating to the best provider for each asset type.
        The order of priority is: NSE Bhavcopy -> AMFI -> yfinance.
        """
        prices_data: Dict[str, Dict[str, Decimal]] = {}

        # 1. Separate assets by type for different providers
        mf_assets = [
            a for a in assets if a.get("asset_type") == "Mutual Fund"
        ]
        indian_market_assets = [
            a for a in assets if a.get("asset_type") in ("STOCK", "BOND", "ETF")
            and a.get("exchange") in ("NSE", "BSE")
        ]
        other_assets = [
            a for a in assets if a not in mf_assets and a not in indian_market_assets
        ]

        # 2. Fetch prices from primary Indian providers
        if indian_market_assets:
            prices_data.update(self.nse_provider.get_current_prices(indian_market_assets))
        if mf_assets:
            prices_data.update(self.amfi_provider.get_current_prices(mf_assets))

        # 3. Use yfinance for any remaining assets (e.g., international)
        #    and as a fallback
        found_tickers = set(prices_data.keys()) # type: ignore
        remaining_assets = other_assets + [
            a for a in indian_market_assets if a["ticker_symbol"] not in found_tickers
        ]

        if remaining_assets:
            prices_data.update(self.yfinance_provider.get_current_prices(remaining_assets))

        return prices_data

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        # Separate assets by type for different providers
        mf_assets = [
            a for a in assets if a.get("asset_type") == "Mutual Fund"
        ]
        other_assets = [
            a for a in assets if a.get("asset_type") != "Mutual Fund"
        ]

        historical_data: Dict[str, Dict[date, Decimal]] = {}

        if other_assets:
            historical_data.update(self.yfinance_provider.get_historical_prices(
                other_assets, start_date, end_date
            ))

        if mf_assets:
            historical_data.update(self.amfi_provider.get_historical_prices(
                mf_assets, start_date, end_date
            ))

        return historical_data

    def get_asset_details(
        self, ticker_symbol: str, asset_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches details for a single asset.
        If asset_type is 'Mutual Fund', it will only check AMFI.
        Otherwise, it will check yfinance.
        """
        if asset_type == "Mutual Fund" or asset_type == "MUTUAL_FUND":
            return self.amfi_provider.get_asset_details(ticker_symbol)

        # Default to yfinance for other types or if type is unknown
        return self.yfinance_provider.get_asset_details(ticker_symbol)

    def search_mutual_funds(self, query: str) -> List[Dict[str, Any]]:
        """Proxy to AMFI provider search."""
        return self.amfi_provider.search(query)

    def get_price_from_yfinance(self, ticker_symbol: str) -> Optional[Decimal]:
        """Proxy to YFinance provider to get a single price."""
        return self.yfinance_provider.get_price(ticker_symbol)


def get_financial_data_service() -> FinancialDataService:
    from app.cache.factory import get_cache_client
    if settings.ENVIRONMENT == "test":
        from app.tests.utils.mock_financial_data import MockFinancialDataService
        return MockFinancialDataService()
    return FinancialDataService(cache_client=get_cache_client())

# Create a singleton instance to be used throughout the application
financial_data_service = get_financial_data_service()
