import csv
import io
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
import yfinance as yf
from pydantic import ValidationError

from app.cache.base import CacheClient
from app.cache.factory import get_cache_client
from app.core.config import settings

# Constants
CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours
CACHE_TTL_AMFI_DATA = 86400  # 24 hours


class AmfiIndiaProvider:
    """
    Provider for fetching and parsing Indian Mutual Fund NAV data from AMFI.
    """

    AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

    def __init__(self, cache_client: Optional[CacheClient]):
        self.cache_client = cache_client

    def _fetch_and_parse_amfi_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetches the raw NAV data from AMFI and parses it into a structured dict
        keyed by scheme code.
        """
        data: Dict[str, Dict[str, Any]] = {}
        try:
            # Use httpx for async-friendly requests, though we use it sync here
            with httpx.Client() as client:
                response = client.get(self.AMFI_URL, timeout=15.0)
                response.raise_for_status()

            # The file is semi-colon delimited. Find the start of the data.
            content = response.text
            lines = content.strip().split("\n")
            first_data_line_index = -1
            for i, line in enumerate(lines):
                if ";" in line and line.split(";", 1)[0].isdigit():
                    first_data_line_index = i
                    break

            if first_data_line_index == -1:
                return {}

            # Use csv reader for robust parsing
            reader = csv.reader(
                io.StringIO("\n".join(lines[first_data_line_index:])),
                delimiter=";",
                skipinitialspace=True,
            )

            for row in reader:
                if len(row) >= 5 and row[0].isdigit():
                    try:
                        scheme_code = row[0]
                        data[scheme_code] = {
                            "scheme_code": scheme_code,
                            "isin": row[1] if row[1] != "N.A." else None,
                            "scheme_name": row[3],
                            "nav": str(Decimal(row[4])) if row[4] != "N.A." else "0.0",
                            "date": (
                                datetime.strptime(row[5], "%d-%b-%Y").date().isoformat()
                                if row[5] != "N.A."
                                else None
                            ),
                        }
                    except (ValueError, IndexError):
                        continue  # Skip malformed rows
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

    def get_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
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

    def search_funds(self, query: str) -> List[Dict[str, Any]]:
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
        """
        Fetches historical NAV for a list of mutual fund assets from mfapi.in.
        """
        historical_data: Dict[str, Dict[date, Decimal]] = defaultdict(dict)
        if not self.cache_client:
            # Caching is highly recommended for this provider
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

                    # The API returns a status field on failure
                    if mf_data.get("status", "").lower() == "fail":
                        print(
                            "WARNING: mfapi.in returned failure for scheme code "
                            f"{scheme_code}."
                        )
                        continue

                    # The data is nested under the 'data' key
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
                            # Skip malformed data points within a successful response
                            continue
                except (
                    httpx.RequestError,
                    httpx.HTTPStatusError,
                    KeyError,
                    ValueError,
                ) as e:
                    # ValueError for JSON decoding errors
                    print(
                        "WARNING: Could not fetch historical NAV for "
                        f"{scheme_code}: {e}"
                    )
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


class YFinanceProvider:
    def __init__(self, cache_client: Optional[CacheClient]):
        self.cache_client = cache_client

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
        prices_data: Dict[str, Dict[str, Decimal]] = {}
        tickers_to_fetch: List[Dict[str, Any]] = []

        if self.cache_client:
            for asset in assets:
                ticker = asset["ticker_symbol"]
                cache_key = f"price_details:{ticker}"
                cached_data = self.cache_client.get_json(cache_key)
                if cached_data:
                    prices_data[ticker] = {
                        "current_price": Decimal(cached_data["current_price"]),
                        "previous_close": Decimal(cached_data["previous_close"]),
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

        if self.cache_client:
            for ticker, data in prices_data.items():
                if any(t["ticker_symbol"] == ticker for t in tickers_to_fetch):
                    serializable_data = {
                        "current_price": str(data["current_price"]),
                        "previous_close": str(data["previous_close"]),
                    }
                    self.cache_client.set_json(
                        f"price_details:{ticker}",
                        serializable_data,
                        expire=CACHE_TTL_CURRENT_PRICE,
                    )

        return prices_data

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        historical_data: Dict[str, Dict[date, Decimal]] = defaultdict(dict)

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

        if self.cache_client:
            serializable_data = {}
            for ticker, date_prices in historical_data.items():
                serializable_data[ticker] = {
                    dt.isoformat(): str(price) for dt, price in date_prices.items()
                }
            self.cache_client.set_json(
                cache_key, serializable_data, expire=CACHE_TTL_HISTORICAL_PRICE
            )

        return historical_data

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches details for a single asset from yfinance.
        Tries to find the asset on NSE, then BSE, then as-is.
        """
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


class FinancialDataService:
    def __init__(self, cache_client: Optional[CacheClient]):
        self.yfinance_provider = YFinanceProvider(cache_client)
        self.amfi_provider = AmfiIndiaProvider(cache_client)

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        # Separate assets by type for different providers
        mf_assets = [
            a
            for a in assets
            if a.get("asset_type") == "Mutual Fund" and a.get("exchange") == "AMFI"
        ]
        other_assets = [
            a
            for a in assets
            if not (
                a.get("asset_type") == "Mutual Fund" and a.get("exchange") == "AMFI"
            )
        ]

        prices_data: Dict[str, Dict[str, Decimal]] = {}

        if other_assets:
            prices_data.update(self.yfinance_provider.get_current_prices(other_assets))

        if mf_assets:
            all_mf_data = self.amfi_provider.get_all_nav_data()
            for asset in mf_assets:
                ticker = asset["ticker_symbol"]
                fund_data = all_mf_data.get(ticker)
                if fund_data and fund_data.get("nav"):
                    nav = Decimal(str(fund_data["nav"]))
                    prices_data[ticker] = {
                        "current_price": nav,
                        "previous_close": nav,  # AMFI doesn't provide prev close
                    }

        return prices_data

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        # Separate assets by type for different providers
        mf_assets = [a for a in assets if a.get("asset_type") == "Mutual Fund"]
        other_assets = [a for a in assets if a.get("asset_type") != "Mutual Fund"]

        historical_data: Dict[str, Dict[date, Decimal]] = defaultdict(dict)

        if other_assets:
            historical_data.update(
                self.yfinance_provider.get_historical_prices(
                    other_assets, start_date, end_date
                )
            )

        if mf_assets:
            historical_data.update(
                self.amfi_provider.get_historical_prices(
                    mf_assets, start_date, end_date
                )
            )

        return historical_data

    def get_asset_details(
        self, ticker_symbol: str, asset_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches details for a single asset.
        If asset_type is 'Mutual Fund', it will only check AMFI.
        Otherwise, it will check yfinance.
        """
        if asset_type == "Mutual Fund":
            return self.amfi_provider.get_details(ticker_symbol)

        # Default to yfinance for other types or if type is unknown
        return self.yfinance_provider.get_asset_details(ticker_symbol)

    def search_mutual_funds(self, query: str) -> List[Dict[str, Any]]:
        """Proxy to AMFI provider search."""
        return self.amfi_provider.search_funds(query)


if settings.ENVIRONMENT == "test":
    from app.tests.utils.mock_financial_data import MockFinancialDataService

    financial_data_service = MockFinancialDataService()
else:
    # Create a singleton instance to be used throughout the application
    financial_data_service = FinancialDataService(cache_client=get_cache_client())
