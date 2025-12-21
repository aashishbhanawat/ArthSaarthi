"""Provider for fetching data from NSE Bhavcopy."""
import csv
import io
import zipfile
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from app.cache.base import CacheClient

from .base import FinancialDataProvider

# --- Constants ---
CACHE_KEY_TEMPLATE = "bhavcopy_data:{date_iso}"
CACHE_TTL = 43200  # 12 hours
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class NseBhavcopyProvider(FinancialDataProvider):
    """
    Provider for fetching and parsing data from the daily NSE Bhavcopy.
    This will be the primary source for Indian market closing prices.
    """

    def __init__(self, cache_client: Optional[CacheClient]):
        self.cache_client = cache_client

    def _get_bhavcopy_url(self, for_date: date) -> tuple[str, str]:
        """
        Constructs the URL and expected filename for the Bhavcopy for a given
        date based on the new format.
        URL: https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip
        Filename: BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv
        """
        # New format as of mid-2024
        # e.g., BhavCopy_NSE_CM_0_0_0_20240726_F_0000.csv.zip
        date_str = for_date.strftime("%Y%m%d")
        filename_prefix = f"BhavCopy_NSE_CM_0_0_0_{date_str}_F_0000"

        # The URL uses nsearchives.nseindia.com
        url = f"https://nsearchives.nseindia.com/content/cm/{filename_prefix}.csv.zip"
        csv_filename = f"{filename_prefix}.csv"
        return url, csv_filename

    def _fetch_and_parse_bhavcopy(
        self, for_date: date
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Fetches, parses, and caches the NSE Bhavcopy for a specific date.
        It tries the given date, then iterates backwards up to 5 days to find the
        most recent available trading day's data.

        Returns a dictionary keyed by BOTH trading symbol AND ISIN for maximum
        lookup flexibility (bonds often use ISIN as ticker_symbol).
        """
        for i in range(5):
            current_date = for_date - timedelta(days=i)
            url, csv_filename = self._get_bhavcopy_url(current_date)

            try:
                with httpx.Client(headers=NSE_HEADERS, follow_redirects=True) as client:
                    response = client.get(url, timeout=20.0)
                    if response.status_code == 404:
                        continue  # Try the previous day
                    response.raise_for_status()

                bhavcopy_data: Dict[str, Dict[str, Decimal]] = {}
                with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
                    with thezip.open(csv_filename) as thefile:
                        # The CSV has headers that need to be normalized
                        # (e.g. "  TckrSymb  ")
                        # DictReader will handle this if we don't specify fieldnames
                        reader = csv.DictReader(io.TextIOWrapper(thefile, "utf-8")) # type: ignore
                        for row in reader:
                            series = row.get("SctySrs", "").strip().upper()
                            # We are interested in a wide range of tradable securities,
                            # not just equities. This includes ETFs, Bonds, etc.
                            # We will exclude series that are typically
                            # non-tradable or special cases.
                            excluded_series = {"IV", "MF", "ME", "RR", "P1"}

                            if series and series not in excluded_series:
                                symbol = row["TckrSymb"].strip().upper()
                                price_data = {
                                    "current_price": Decimal(
                                        row["ClsPric"].strip().replace(",", "")),
                                    "previous_close": Decimal(
                                        row["PrvsClsgPric"].strip().replace(",", "")),
                                }
                                # Index by trading symbol
                                bhavcopy_data[symbol] = price_data

                                # Also index by ISIN if present (for bonds that use
                                # ISIN as ticker_symbol)
                                isin = row.get("ISIN", "").strip().upper()
                                if isin and isin != symbol:
                                    bhavcopy_data[isin] = price_data

                return bhavcopy_data
            except (httpx.RequestError, KeyError, zipfile.BadZipFile, csv.Error) as e:
                print(f"INFO: Failed to fetch/parse Bhavcopy for {current_date} "
                      f"from {url}. Error: {e}. Trying previous day.")
                continue

        print(f"ERROR: Could not fetch Bhavcopy for the last 5 days from {for_date}.")
        return {}

    def _get_bhavcopy_data(
        self, for_date: Optional[date] = None
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Main method to get Bhavcopy data, utilizing the cache.
        """
        today = for_date or date.today()
        cache_key = CACHE_KEY_TEMPLATE.format(date_iso=today.isoformat())

        if self.cache_client:
            cached_data = self.cache_client.get_json(cache_key)
            if cached_data:
                # Deserialize from string back to Decimal
                return {
                    symbol: {
                        "current_price": Decimal(prices["current_price"]),
                        "previous_close": Decimal(prices["previous_close"]),
                    }
                    for symbol, prices in cached_data.items()
                }

        fresh_data = self._fetch_and_parse_bhavcopy(for_date=today)
        if fresh_data and self.cache_client:
            # Serialize Decimal to string for JSON compatibility
            serializable_data = {
                symbol: {
                    "current_price": str(prices["current_price"]),
                    "previous_close": str(prices["previous_close"]),
                }
                for symbol, prices in fresh_data.items()
            }
            self.cache_client.set_json(cache_key, serializable_data, expire=CACHE_TTL)

        return fresh_data

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        """Fetches current and previous day's close price for a list of assets."""
        bhavcopy_data = self._get_bhavcopy_data()
        if not bhavcopy_data:
            return {}

        prices: Dict[str, Dict[str, Decimal]] = {}
        for asset in assets:
            ticker = asset.get("ticker_symbol")
            if ticker and ticker in bhavcopy_data:
                prices[ticker] = bhavcopy_data[ticker]

        return prices

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        """Historical prices are not available from a single Bhavcopy."""
        # This could be implemented by fetching and storing daily bhavcopies,
        # but that is a significant undertaking. For now, return empty.
        return {}

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """Asset details are not the primary purpose of this provider."""
        return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search is not supported by the Bhavcopy provider."""
        return []
