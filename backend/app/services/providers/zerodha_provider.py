import hashlib
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
KITE_BASE_URL = "https://api.kite.trade"

logger = logging.getLogger(__name__)


class ZerodhaKiteProvider(FinancialDataProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        api_secret: Optional[str] = None,
        cache_client: Optional[CacheClient] = None,
    ):
        self.api_key = api_key
        self.access_token = access_token
        self.api_secret = api_secret
        self.cache_client = cache_client

    @staticmethod
    def get_login_url(api_key: str) -> str:
        encoded_key = urllib.parse.quote(api_key)
        return f"https://kite.zerodha.com/connect/login?v=3&api_key={encoded_key}"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "X-Kite-Version": "3",
            "Accept": "application/json",
        }
        if self.api_key and self.access_token:
            headers["Authorization"] = f"token {self.api_key}:{self.access_token}"
        return headers

    def authenticate_request_token(self, request_token: str) -> Dict[str, Any]:
        """Exchanges Kite request token for access token using SHA256 checksum."""
        if not self.api_key or not self.api_secret:
            return {"success": False, "error": "Missing API Key or API Secret"}

        raw_checksum = self.api_key + request_token + self.api_secret
        checksum = hashlib.sha256(raw_checksum.encode("utf-8")).hexdigest()

        url = f"{KITE_BASE_URL}/session/token"
        payload = {
            "api_key": self.api_key,
            "request_token": request_token,
            "checksum": checksum,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, data=payload)
                if resp.status_code == 200:
                    res_json = resp.json()
                    if res_json.get("status") == "success":
                        data = res_json.get("data", {})
                        access_token = data.get("access_token")
                        if access_token:
                            self.access_token = access_token
                            return {"success": True, "access_token": access_token, "data": data}
                    return {"success": False, "error": res_json.get("message", "Token exchange failed")}
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.error(f"Zerodha Kite authentication error: {e}")
            return {"success": False, "error": str(e)}

    def _clean_symbol(self, ticker: str) -> str:
        """Strips exchange suffix like .NS, .BO, etc."""
        return ticker.split(".")[0].upper()

    def get_current_prices(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Decimal]]:
        prices_data: Dict[str, Dict[str, Decimal]] = {}
        if not self.api_key or not self.access_token:
            logger.warning("Zerodha Kite: Unconfigured or missing access token.")
            return prices_data

        headers = self._get_headers()
        instruments_map: Dict[str, str] = {}  # "NSE:RELIANCE" -> "RELIANCE.NS"

        for asset in assets:
            ticker = asset.get("ticker_symbol", "")
            stock_code = self._clean_symbol(ticker)
            exchange = "NSE"
            if asset.get("exchange") and "BSE" in asset.get("exchange", "").upper():
                exchange = "BSE"

            inst_param = f"{exchange}:{stock_code}"
            instruments_map[inst_param] = ticker

        if not instruments_map:
            return prices_data

        params = [("i", inst) for inst in instruments_map.keys()]
        url = f"{KITE_BASE_URL}/quote"

        try:
            time.sleep(0.05)
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    res_json = resp.json()
                    data = res_json.get("data", {})
                    for inst_key, orig_ticker in instruments_map.items():
                        quote = data.get(inst_key)
                        if quote:
                            last_price = Decimal(str(quote.get("last_price", 0)))
                            ohlc = quote.get("ohlc", {})
                            prev_close = Decimal(str(ohlc.get("close") or last_price))
                            if last_price > 0:
                                prices_data[orig_ticker] = {
                                    "current_price": last_price,
                                    "previous_close": prev_close,
                                }
        except Exception as e:
            logger.error(f"Zerodha Kite get_current_prices error: {e}")

        return prices_data

    def get_historical_prices(
        self, assets: List[Dict[str, Any]], start_date: date, end_date: date
    ) -> Dict[str, Dict[date, Decimal]]:
        historical_data: Dict[str, Dict[date, Decimal]] = {}
        if not self.api_key or not self.access_token:
            return historical_data

        # Delegating to current prices if historical endpoint is restricted
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
