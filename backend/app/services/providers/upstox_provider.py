"""
Provider for fetching market data from Upstox API v3.
Uses public unauthenticated endpoints for historical candle data and market holidays.
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.cache.base import CacheClient
from app.services.upstox_metadata_service import UpstoxMetadataService

from .base import FinancialDataProvider

CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours
UPSTOX_V3_CANDLE_URL = "https://api.upstox.com/v3/historical-candle"

logger = logging.getLogger(__name__)


class UpstoxProvider(FinancialDataProvider):
    def __init__(self, cache_client: Optional[CacheClient] = None):
        self.cache_client = cache_client
        self.metadata_service = UpstoxMetadataService(cache_client)

    def _fetch_upstox_candles(
        self,
        instrument_key: str,
        unit: str,
        interval: str,
        to_date: date,
        from_date: date,
    ) -> List[List[Any]]:
        """
        Fetches OHLCV candle data from Upstox V3 public API endpoint without auth.
        URL format: GET /v3/historical-candle/:key/:unit/:interval/:to/:from
        """
        encoded_key = urllib.parse.quote(instrument_key, safe="")
        url = (
            f"{UPSTOX_V3_CANDLE_URL}/{encoded_key}/{unit}/{interval}/"
            f"{to_date.isoformat()}/{from_date.isoformat()}"
        )

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if payload.get("status") == "success":
                    return payload.get("data", {}).get("candles", [])
                else:
                    logger.warning(
                        "Upstox API returned error status for "
                        f"{instrument_key}: {payload}"
                    )
        except Exception as e:
            logger.warning(
                f"Error fetching Upstox V3 candles for {instrument_key}: {e}"
            )

        return []

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Fetches current and previous day's close price for a list of assets.
        Uses public Upstox V3 historical candle endpoint.
        """
        prices_data: Dict[str, Dict[str, Decimal]] = {}
        assets_to_fetch: List[Dict[str, Any]] = []

        if self.cache_client:
            for asset in assets:
                ticker = asset.get("ticker_symbol", "")
                isin = asset.get("isin")
                inst_key = self.metadata_service.get_instrument_key(ticker, isin)
                if not inst_key:
                    continue

                cache_key = f"price_details:upstox:{inst_key}"
                not_found_cache_key = f"asset_not_found:upstox:{inst_key}"

                cached_data = self.cache_client.get_json(cache_key)
                if cached_data:
                    prices_data[ticker] = {
                        "current_price": Decimal(cached_data["current_price"]),
                        "previous_close": Decimal(cached_data["previous_close"]),
                    }
                    continue

                if not self.cache_client.get_json(not_found_cache_key):
                    assets_to_fetch.append(asset)
        else:
            assets_to_fetch = assets

        if not assets_to_fetch:
            return prices_data

        today = date.today()
        # Fetch last 10 days to handle long holiday weekends safely
        from_date = today - timedelta(days=10)

        for asset in assets_to_fetch:
            ticker = asset.get("ticker_symbol", "")
            isin = asset.get("isin")
            inst_key = self.metadata_service.get_instrument_key(ticker, isin)

            if not inst_key:
                logger.debug(
                    f"Upstox: Could not resolve instrument key for ticker {ticker}"
                )
                continue

            # Respect rate limits: 50 req/sec max -> 20ms sleep between requests
            time.sleep(0.02)

            candles = self._fetch_upstox_candles(
                inst_key, "days", "1", today, from_date
            )

            if candles and len(candles) >= 1:
                # Structure: [timestamp, open, high, low, close, volume, oi]
                latest_close = Decimal(str(candles[0][4]))
                previous_close = (
                    Decimal(str(candles[1][4])) if len(candles) >= 2 else latest_close
                )

                prices_data[ticker] = {
                    "current_price": latest_close,
                    "previous_close": previous_close,
                }

                if self.cache_client:
                    self.cache_client.set_json(
                        f"price_details:upstox:{inst_key}",
                        {
                            "current_price": str(latest_close),
                            "previous_close": str(previous_close),
                        },
                        expire=CACHE_TTL_CURRENT_PRICE,
                    )
            else:
                if self.cache_client:
                    self.cache_client.set_json(
                        f"asset_not_found:upstox:{inst_key}",
                        {"not_found": True},
                        expire=CACHE_TTL_CURRENT_PRICE,
                    )

        return prices_data

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        """
        Fetches historical prices for a list of assets over a date range.
        """
        historical_data: Dict[str, Dict[date, Decimal]] = defaultdict(dict)

        for asset in assets:
            ticker = asset.get("ticker_symbol", "")
            isin = asset.get("isin")
            inst_key = self.metadata_service.get_instrument_key(ticker, isin)

            if not inst_key:
                continue

            s_iso = start_date.isoformat()
            e_iso = end_date.isoformat()
            cache_key = f"history:upstox:{inst_key}:{s_iso}:{e_iso}"
            if self.cache_client:
                cached_data = self.cache_client.get_json(cache_key)
                if cached_data:
                    for dt_str, price_str in cached_data.items():
                        c_dt = date.fromisoformat(dt_str)
                        historical_data[ticker][c_dt] = Decimal(price_str)
                    continue

            # Respect rate limits: 20ms sleep
            time.sleep(0.02)
            candles = self._fetch_upstox_candles(
                inst_key, "days", "1", end_date, start_date
            )

            if candles:
                asset_history = {}
                for candle in candles:
                    dt_str = candle[0].split("T")[0]
                    c_date = date.fromisoformat(dt_str)
                    close_price = Decimal(str(candle[4]))
                    historical_data[ticker][c_date] = close_price
                    asset_history[dt_str] = str(close_price)

                if self.cache_client:
                    self.cache_client.set_json(
                        cache_key, asset_history, expire=CACHE_TTL_HISTORICAL_PRICE
                    )

        return historical_data

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """Looking up basic asset details from metadata service."""
        inst_key = self.metadata_service.get_instrument_key(ticker_symbol)
        if inst_key:
            return {
                "name": ticker_symbol,
                "asset_type": "Stock",
                "exchange": "NSE" if "NSE" in inst_key else "BSE",
                "currency": "INR",
            }
        return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Searches for assets supported by Upstox metadata."""
        inst_key = self.metadata_service.get_instrument_key(query)
        if inst_key:
            return [{
                "ticker_symbol": query.upper(),
                "name": query.upper(),
                "exchange": "NSE",
                "asset_type": "STOCK",
                "currency": "INR",
            }]
        return []
