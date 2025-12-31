"""Provider for fetching data from AMFI (Association of Mutual Funds in India)."""
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from app.cache.base import CacheClient
from app.cache.factory import get_cache_client

from .base import FinancialDataProvider

CACHE_TTL_AMFI_DATA = 86400  # 24 hours
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours


class AmfiIndiaProvider(FinancialDataProvider):
    """
    Provider for fetching and parsing Indian Mutual Fund NAV data from AMFI.
    """

    AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

    def __init__(self, cache_client: Optional[CacheClient]):
        self.cache_client = cache_client

    def _parse_category_header(self, line: str) -> tuple[str | None, str | None]:
        """
        Parses category headers from NAVALL.txt.
        Example: "Open Ended Schemes(Equity Scheme - Large Cap Fund)"
        Returns: ("Equity Scheme", "Large Cap Fund")
        """
        import re
        # Match pattern: "Open Ended Schemes(Category - Sub Category)"
        # or "Close Ended Schemes(Category - Sub Category)"
        match = re.match(
            r"(?:Open|Close) Ended Schemes\s*\(([^)]+)\)", line.strip()
        )
        if match:
            inner = match.group(1).strip()
            if " - " in inner:
                parts = inner.split(" - ", 1)
                return parts[0].strip(), parts[1].strip()
            return inner, None
        return None, None

    def _fetch_and_parse_amfi_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetches the raw NAV data from AMFI and parses it into a structured dict
        keyed by scheme code. Also extracts MF category from header lines.
        """
        data: Dict[str, Dict[str, Any]] = {}
        current_category: str | None = None
        current_sub_category: str | None = None

        try:
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(self.AMFI_URL, timeout=15.0)
                response.raise_for_status()

            content = response.text
            lines = content.strip().split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check if this is a category header line
                cat, sub_cat = self._parse_category_header(line)
                if cat:
                    current_category = cat
                    current_sub_category = sub_cat
                    continue

                # Parse data rows (scheme code;ISIN;ISIN2;name;NAV;date)
                if ";" in line:
                    parts = line.split(";")
                    if len(parts) >= 5 and parts[0].isdigit():
                        try:
                            scheme_code = parts[0]
                            data[scheme_code] = {
                                "scheme_code": scheme_code,
                                "isin": parts[1] if parts[1] != "N.A." else None,
                                "isin2": (
                                    parts[2] if len(parts) > 2 and parts[2] != "N.A."
                                    else None
                                ),
                                "scheme_name": parts[3],
                                "nav": (
                                    str(Decimal(parts[4]))
                                    if parts[4] != "N.A." else "0.0"
                                ),
                                "date": (
                                    datetime.strptime(
                                        parts[5], "%d-%b-%Y"
                                    ).date().isoformat()
                                    if len(parts) > 5 and parts[5] != "N.A."
                                    else None
                                ),
                                "mf_category": current_category,
                                "mf_sub_category": current_sub_category,
                            }
                        except (ValueError, IndexError):
                            continue
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"ERROR: Could not fetch AMFI data: {e}")

        return data

    def get_all_nav_data(self) -> Dict[str, Dict[str, Any]]:
        """Retrieves all NAV data, using a cache if available."""
        if not self.cache_client:
            return self._fetch_and_parse_amfi_data()

        cache_key = "amfi_nav_data"
        cached_data = self.cache_client.get_json(cache_key)
        if cached_data:
            return cached_data

        fresh_data = self._fetch_and_parse_amfi_data()
        if fresh_data:
            self.cache_client.set_json(
                cache_key, fresh_data, expire=CACHE_TTL_AMFI_DATA
            )
        return fresh_data

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """Gets the details for a given MF scheme code."""
        all_data = self.get_all_nav_data()
        fund_data = all_data.get(ticker_symbol)
        if not fund_data:
            return None

        return {
            "name": fund_data.get("scheme_name"),
            "asset_type": "Mutual Fund",
            "exchange": "AMFI",
            "currency": "INR",
            "isin": fund_data.get("isin"),
        }

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Searches for funds by name or scheme code."""
        query = query.lower()
        all_data = self.get_all_nav_data()

        results = []
        for scheme_code, details in all_data.items():
            if query in scheme_code or query in details["scheme_name"].lower():
                results.append(
                    {
                        "ticker_symbol": scheme_code,
                        "name": details["scheme_name"],
                        "asset_type": "Mutual Fund",
                    }
                )
        return results[:50]  # Limit results

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        """Fetches historical NAV for a list of mutual fund assets from mfapi.in."""
        historical_data: Dict[str, Dict[date, Decimal]] = defaultdict(dict)
        if not self.cache_client:
            pass

        mf_tickers_str = ",".join(sorted([a["ticker_symbol"] for a in assets]))
        cache_key = (
            f"mf_history:{mf_tickers_str}:{start_date.isoformat()}:"
            f"{end_date.isoformat()}"
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

        with httpx.Client() as client:
            for asset in assets:
                scheme_code = asset["ticker_symbol"]
                try:
                    response = client.get(
                        f"https://api.mfapi.in/mf/{scheme_code}", timeout=10.0
                    )
                    response.raise_for_status()
                    mf_data = response.json()

                    if mf_data.get("status", "").lower() == "fail":
                        continue

                    for nav_point in mf_data.get("data", []):
                        try:
                            nav_date = datetime.strptime(
                                nav_point["date"], "%d-%m-%Y"
                            ).date()
                            if start_date <= nav_date <= end_date:
                                historical_data[scheme_code][nav_date] = Decimal(
                                    nav_point["nav"]
                                )
                        except (ValueError, KeyError):
                            continue
                except (httpx.RequestError, httpx.HTTPStatusError, KeyError,
                        ValueError):
                    continue

        if self.cache_client and historical_data:
            serializable_data = {
                t: {d.isoformat(): str(p) for d, p in dp.items()}
                for t, dp in historical_data.items()
            }
            self.cache_client.set_json(
                cache_key, serializable_data, expire=CACHE_TTL_HISTORICAL_PRICE
            )

        return historical_data

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        """Gets current prices for mutual funds from the main AMFI data dump."""
        prices: Dict[str, Dict[str, Decimal]] = {}
        all_data = self.get_all_nav_data()
        for asset in assets:
            ticker = asset["ticker_symbol"]
            fund_data = all_data.get(ticker)
            if fund_data and fund_data.get("nav"):
                nav = Decimal(str(fund_data["nav"]))
                prices[ticker] = {"current_price": nav, "previous_close": nav}
        return prices


amfi_provider = AmfiIndiaProvider(cache_client=get_cache_client())
