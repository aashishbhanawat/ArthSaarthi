import json
import logging
import time
import urllib.parse
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from app.cache.base import CacheClient
from .base import FinancialDataProvider

CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours
BREEZE_BASE_URL = "https://api.icicidirect.com/breezeapi/v1"

logger = logging.getLogger(__name__)


class IciciBreezeProvider(FinancialDataProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        session_token: Optional[str] = None,
        api_secret: Optional[str] = None,
        cache_client: Optional[CacheClient] = None,
    ):
        self.api_key = api_key
        self.session_token = session_token
        self.api_secret = api_secret
        self.cache_client = cache_client

    @staticmethod
    def get_login_url(api_key: str) -> str:
        encoded_key = urllib.parse.quote(api_key)
        return f"https://api.icicidirect.com/apiuser/login?api_key={encoded_key}"


    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.session_token:
            headers["X-SessionToken"] = self.session_token
        if self.api_key:
            headers["X-AppKey"] = self.api_key
        return headers

    def authenticate_session(self, session_token: str) -> Dict[str, Any]:
        """Exchanges/verifies ICICI Breeze session token with customer details endpoint."""
        url = f"{BREEZE_BASE_URL}/customerdetails"
        self.session_token = session_token
        headers = self._get_headers()
        payload = {"SessionToken": session_token, "AppKey": self.api_key}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers, params=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("Status") == 200 or data.get("status") == 200:
                        return {"success": True, "data": data.get("Success", {})}
                    return {"success": False, "error": data.get("Error", "Authentication failed")}
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.error(f"ICICI Breeze authentication error: {e}")
            return {"success": False, "error": str(e)}

    def _clean_symbol(self, ticker: str) -> str:
        """Strips exchange suffix like .NS, .BO, etc."""
        return ticker.split(".")[0].upper()

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        prices_data: Dict[str, Dict[str, Decimal]] = {}
        if not self.api_key or not self.session_token:
            logger.warning("ICICI Breeze: Unconfigured or missing session token.")
            return prices_data

        headers = self._get_headers()
        for asset in assets:
            ticker = asset.get("ticker_symbol", "")
            stock_code = self._clean_symbol(ticker)
            exchange_code = "NSE"
            if asset.get("exchange") and "BSE" in asset.get("exchange", "").upper():
                exchange_code = "BSE"

            cache_key = f"price_details:icici:{stock_code}"
            if self.cache_client:
                cached = self.cache_client.get_json(cache_key)
                if cached:
                    prices_data[ticker] = {
                        "current_price": Decimal(cached["current_price"]),
                        "previous_close": Decimal(cached["previous_close"]),
                    }
                    continue

            url = f"{BREEZE_BASE_URL}/stockquotes"
            params = {
                "stock_code": stock_code,
                "exchange_code": exchange_code,
            }

            try:
                time.sleep(0.05)  # Rate limit safety
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(url, headers=headers, params=params)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        success_data = res_json.get("Success")
                        if success_data and len(success_data) > 0:
                            quote = success_data[0]
                            lTP = Decimal(str(quote.get("lTP") or quote.get("ltp") or 0))
                            close = Decimal(str(quote.get("previous_close") or quote.get("close") or lTP))
                            if lTP > 0:
                                prices_data[ticker] = {
                                    "current_price": lTP,
                                    "previous_close": close,
                                }
                                if self.cache_client:
                                    self.cache_client.set_json(
                                        cache_key,
                                        {"current_price": str(lTP), "previous_close": str(close)},
                                        expire=CACHE_TTL_CURRENT_PRICE,
                                    )
            except Exception as e:
                logger.error(f"ICICI Breeze price fetch error for {stock_code}: {e}")

        return prices_data

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        historical_data: Dict[str, Dict[date, Decimal]] = {}
        if not self.api_key or not self.session_token:
            return historical_data

        headers = self._get_headers()
        for asset in assets:
            ticker = asset.get("ticker_symbol", "")
            stock_code = self._clean_symbol(ticker)
            exchange_code = "NSE"
            if asset.get("exchange") and "BSE" in asset.get("exchange", "").upper():
                exchange_code = "BSE"

            url = f"{BREEZE_BASE_URL}/historicalcharts"
            params = {
                "from_date": f"{start_date.isoformat()}T07:00:00.000Z",
                "to_date": f"{end_date.isoformat()}T19:00:00.000Z",
                "stock_code": stock_code,
                "exchange_code": exchange_code,
                "interval": "1day",
            }

            try:
                time.sleep(0.05)
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url, headers=headers, params=params)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        candles = res_json.get("Success", [])
                        if candles:
                            historical_data[ticker] = {}
                            for c in candles:
                                dt_str = c.get("datetime", "").split(" ")[0].split("T")[0]
                                if dt_str:
                                    c_dt = date.fromisoformat(dt_str)
                                    close_px = Decimal(str(c.get("close", 0)))
                                    historical_data[ticker][c_dt] = close_px
            except Exception as e:
                logger.error(f"ICICI Breeze historical prices error for {stock_code}: {e}")

        return historical_data

    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        stock_code = self._clean_symbol(ticker_symbol)
        return {
            "name": stock_code,
            "asset_type": "STOCK",
            "exchange": "NSE",
            "currency": "INR",
        }

    def search(self, query: str) -> List[Dict[str, Any]]:
        clean_q = self._clean_symbol(query)
        if not clean_q:
            return []
        return [{
            "ticker_symbol": clean_q,
            "name": clean_q,
            "exchange": "NSE",
            "asset_type": "STOCK",
            "currency": "INR",
        }]
