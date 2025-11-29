import logging
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

logger = logging.getLogger(__name__)


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
        The order of priority is now asset-specific for better accuracy:
        - Stocks: yfinance -> NSE
        - Mutual Funds: AMFI -> NSE
        - Bonds: NSE
        """
        logger.debug(f"get_current_prices called for assets: {assets}")
        prices_data: Dict[str, Dict[str, Decimal]] = {}

        # 1. Separate assets by type for different providers
        mf_assets = [a for a in assets if a.get("asset_type") == "Mutual Fund"]
        stock_assets = [
            a for a in assets if str(a.get("asset_type")).upper() in ("STOCK", "ETF")
        ]
        bond_assets = [a for a in assets if str(a.get("asset_type")).upper() == "BOND"]
        other_assets = [
            a for a in assets
            if a not in mf_assets and a not in stock_assets and a not in bond_assets
        ]

        # --- Processing by Priority ---

        # 2. Mutual Funds: AMFI is the primary source.
        if mf_assets:
            logger.debug(f"Processing {len(mf_assets)} MF assets with AMFI provider.")
            prices_data.update(self.amfi_provider.get_current_prices(mf_assets))
            logger.debug(f"Prices after AMFI: {prices_data.keys()}")

        # 3. Stocks: yfinance is the primary source for real-time data.
        #    Append .NS for Indian stocks as required by yfinance.
        if stock_assets:
            logger.debug(
                f"Processing {len(stock_assets)} stock assets with yfinance provider."
            )
            logger.debug(
                "Tickers sent to yfinance: "
                f"{[a['ticker_symbol'] for a in stock_assets]}"
            )
            prices_data.update(
                self.yfinance_provider.get_current_prices(stock_assets)
            )
            logger.debug(f"Prices after yfinance: {prices_data.keys()}")

        # 4. Bonds: NSE is the primary source.
        if bond_assets:
            logger.debug(
                f"Processing {len(bond_assets)} bond assets with NSE provider."
            )
            prices_data.update(self.nse_provider.get_current_prices(bond_assets))
            logger.debug(f"Prices after NSE (for bonds): {prices_data.keys()}")

        # 5. NSE Fallback: For any stocks or MFs not found by their primary provider,
        #    try the NSE provider.
        # We need to strip the '.NS' suffix from the found tickers for a correct
        # comparison.
        found_tickers_cleaned = {t.replace('.NS', '') for t in prices_data.keys()}

        nse_fallback_candidates = stock_assets + mf_assets
        nse_fallback_needed = [
            a
            for a in nse_fallback_candidates
            if a.get("ticker_symbol") not in found_tickers_cleaned
        ]
        if nse_fallback_needed:
            logger.debug(
                f"Found {len(nse_fallback_needed)} assets needing NSE fallback."
            )
            logger.debug(
                "Tickers for NSE fallback: "
                f"{[a['ticker_symbol'] for a in nse_fallback_needed]}"
            )
            prices_data.update(
                self.nse_provider.get_current_prices(nse_fallback_needed)
            )
            logger.debug(f"Prices after NSE fallback: {prices_data.keys()}")

        # 6. Final yfinance Fallback: For any remaining international or other assets.
        if other_assets:
            logger.debug(f"Processing {len(other_assets)} other assets with yfinance.")
            prices_data.update(self.yfinance_provider.get_current_prices(other_assets))

        logger.debug(f"Final prices returned: {prices_data}")
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

    def get_exchange_rate(
        self, from_currency: str, to_currency: str, date_obj: date
    ) -> Optional[Decimal]:
        """
        Fetches the exchange rate between two currencies for a specific date.
        Delegates to yfinance provider.
        """
        return self.yfinance_provider.get_exchange_rate(
            from_currency, to_currency, date_obj
        )


def get_financial_data_service() -> FinancialDataService:
    from app.cache.factory import get_cache_client
    if settings.ENVIRONMENT == "test":
        from app.tests.utils.mock_financial_data import MockFinancialDataService
        return MockFinancialDataService()
    return FinancialDataService(cache_client=get_cache_client())

# Create a singleton instance to be used throughout the application
financial_data_service = get_financial_data_service()
