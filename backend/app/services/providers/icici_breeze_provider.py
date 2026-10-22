import hashlib
import json
import logging
import time
import urllib.parse
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from app.cache.base import CacheClient

from .base import FinancialDataProvider

CACHE_TTL_CURRENT_PRICE = 900  # 15 minutes
CACHE_TTL_HISTORICAL_PRICE = 86400  # 24 hours
BREEZE_BASE_URL = "https://api.icicidirect.com/breezeapi/api/v1"


logger = logging.getLogger(__name__)


def _compute_breeze_header_signature(val1: str, val2: str, val3: str) -> str:
    """Computes SHA-256 header checksum required by ICICI Breeze Direct API protocol."""
    payload = f"{val1}{val2}{val3}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()  # noqa: S324


class IciciBreezeProvider(FinancialDataProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        session_token: Optional[str] = None,
        api_secret: Optional[str] = None,
        cache_client: Optional[CacheClient] = None,
    ):
        self.api_key = api_key.strip() if api_key else None
        self.session_token = session_token.strip() if session_token else None
        self.api_secret = api_secret.strip() if api_secret else None
        self.cache_client = cache_client

    @staticmethod
    def get_login_url(api_key: str) -> str:
        encoded_key = urllib.parse.quote(api_key.strip() if api_key else "")
        return f"https://api.icicidirect.com/apiuser/login?api_key={encoded_key}"

    def _get_headers(self, payload_str: str = "") -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.session_token:
            headers["X-SessionToken"] = self.session_token
            headers["SessionToken"] = self.session_token
        if self.api_key:
            headers["X-AppKey"] = self.api_key

        if self.api_secret:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            checksum = _compute_breeze_header_signature(
                timestamp, payload_str, self.api_secret
            )
            headers["X-Timestamp"] = timestamp
            headers["X-Checksum"] = f"token {checksum}"

        return headers

    def authenticate_session(self, session_token: str) -> Dict[str, Any]:
        """Exchanges/verifies ICICI Breeze session token with customer details endpoint using GET."""
        url = f"{BREEZE_BASE_URL}/customerdetails"
        self.session_token = session_token.strip() if session_token else None
        headers = self._get_headers("")
        params = {
            "SessionToken": self.session_token or "",
            "AppKey": self.api_key or "",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    status_val = data.get("Status") or data.get("status")
                    if status_val in (200, "200"):
                        success_data = data.get("Success", {})
                        returned_token = None
                        if isinstance(success_data, dict):
                            returned_token = success_data.get("session_token") or success_data.get("SessionToken")
                        elif isinstance(data, dict):
                            returned_token = data.get("session_token") or data.get("SessionToken")

                        if returned_token and isinstance(returned_token, str):
                            self.session_token = returned_token.strip()

                        return {
                            "success": True,
                            "data": success_data,
                            "session_token": self.session_token,
                        }
                    else:
                        err_msg = data.get("Error") or data.get("error") or f"Customerdetails status {status_val}"
                        logger.error(f"ICICI Breeze customerdetails error: {err_msg}")
                        return {"success": False, "error": str(err_msg)}
                else:
                    logger.error(f"ICICI Breeze customerdetails HTTP {resp.status_code}: {resp.text}")
                    return {"success": False, "error": f"ICICI Breeze API HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.error(f"ICICI Breeze authentication exception: {e}")
            return {"success": False, "error": f"Connection/auth exception: {e}"}

    def _check_res_for_token_error(self, res_json: Dict[str, Any]) -> None:
        if not isinstance(res_json, dict):
            return
        status_val = str(res_json.get("Status") or res_json.get("status") or "")
        err_msg = str(res_json.get("Error") or res_json.get("error") or "").lower()
        if status_val in ("401", "403") or any(
            kw in err_msg for kw in ("token", "session", "unauthorized", "expired", "invalid")
        ):
            logger.error(f"ICICI Breeze API returned session error: {res_json}")
            raise PermissionError("BROKER_TOKEN_EXPIRED")

    def _make_get_call(
        self, client: httpx.Client, url: str, body_dict: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Executes an authenticated GET request with Breeze SHA256 checksum over compact JSON body."""
        body_json = json.dumps(body_dict, separators=(",", ":")) if body_dict else ""
        headers = self._get_headers(body_json)
        return client.request("GET", url, content=body_json.encode("utf-8"), headers=headers)

    def fetch_holdings(
        self, exchange_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetches current portfolio holdings directly from ICICI Breeze API across exchanges (NSE, BSE).

        Refer: https://api.icicidirect.com/breezeapi/documents/index.html#portfolioholdings
        """
        if not self.api_key or not self.session_token:
            logger.warning("ICICI Breeze: Cannot fetch holdings without API key and session token.")
            raise PermissionError("BROKER_TOKEN_EXPIRED")

        url = f"{BREEZE_BASE_URL}/portfolioholdings"
        target_exchanges = exchange_codes or ["NSE", "BSE"]
        all_holdings: List[Dict[str, Any]] = []
        auth_error_encountered = False

        logger.info("Executing ICICI Breeze fetch_holdings API call for %s...", target_exchanges)
        try:
            with httpx.Client(timeout=15.0) as client:
                for exc in target_exchanges:
                    try:
                        resp = self._make_get_call(client, url, {"exchange_code": exc})
                        logger.info(
                            "ICICI Breeze fetch_holdings (%s) HTTP status: %s",
                            exc,
                            resp.status_code,
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            self._check_res_for_token_error(res_json)
                            success_data = res_json.get("Success")
                            if success_data and isinstance(success_data, list):
                                logger.info(
                                    "Fetched %d holdings for exchange %s from ICICI Breeze.",
                                    len(success_data),
                                    exc,
                                )
                                all_holdings.extend(success_data)
                        elif resp.status_code in (401, 403):
                            logger.error(
                                "ICICI Breeze session token expired or invalid (HTTP %s).",
                                resp.status_code,
                            )
                            auth_error_encountered = True
                            break
                        else:
                            logger.warning(
                                "ICICI Breeze fetch_holdings (%s) returned HTTP %s: %s",
                                exc,
                                resp.status_code,
                                resp.text,
                            )
                    except PermissionError:
                        auth_error_encountered = True
                        break
                    except Exception as exc_err:
                        logger.warning(
                            "ICICI Breeze fetch_holdings exchange %s error: %s",
                            exc,
                            exc_err,
                        )

            if auth_error_encountered:
                raise PermissionError("BROKER_TOKEN_EXPIRED")

            logger.info("Successfully fetched %d total holdings from ICICI Breeze.", len(all_holdings))
            return all_holdings
        except PermissionError:
            raise
        except Exception as e:
            logger.error("ICICI Breeze fetch_holdings error: %s", e, exc_info=True)
            raise

    def fetch_trades(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetches trade book / executed order list directly from ICICI Breeze API.

        Refer: https://api.icicidirect.com/breezeapi/documents/index.html#getorderlist
        Uses /order (order list) with fallback to /orderlist and /trades.
        """
        if not self.api_key or not self.session_token:
            logger.warning("ICICI Breeze: Cannot fetch trades without API key and session token.")
            raise PermissionError("BROKER_TOKEN_EXPIRED")

        target_exchanges = exchange_codes or ["NSE", "BSE"]
        from_date_str = (
            f"{from_date.isoformat()}T00:00:00.000Z"
            if from_date
            else "2020-01-01T00:00:00.000Z"
        )
        to_date_str = (
            f"{to_date.isoformat()}T23:59:59.000Z"
            if to_date
            else datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59.000Z")
        )

        all_orders: List[Dict[str, Any]] = []
        auth_error_encountered = False

        endpoints_to_try = [
            f"{BREEZE_BASE_URL}/order",
            f"{BREEZE_BASE_URL}/orderlist",
            f"{BREEZE_BASE_URL}/trades",
        ]

        logger.info(
            "Executing ICICI Breeze fetch_trades API call from %s to %s for %s...",
            from_date_str,
            to_date_str,
            target_exchanges,
        )

        try:
            with httpx.Client(timeout=15.0) as client:
                for exc in target_exchanges:
                    body = {
                        "exchange_code": exc,
                        "from_date": from_date_str,
                        "to_date": to_date_str,
                    }
                    fetched_for_exc = False

                    for endpoint_url in endpoints_to_try:
                        try:
                            resp = self._make_get_call(client, endpoint_url, body)
                            if resp.status_code == 404:
                                logger.debug(
                                    "Endpoint %s returned 404, trying next endpoint...",
                                    endpoint_url,
                                )
                                continue

                            logger.info(
                                "ICICI Breeze %s (%s) HTTP status: %s",
                                endpoint_url.split("/")[-1],
                                exc,
                                resp.status_code,
                            )

                            if resp.status_code == 200:
                                res_json = resp.json()
                                self._check_res_for_token_error(res_json)
                                success_data = res_json.get("Success")
                                if success_data and isinstance(success_data, list):
                                    logger.info(
                                        "Fetched %d orders/trades for %s from ICICI Breeze (%s).",
                                        len(success_data),
                                        exc,
                                        endpoint_url.split("/")[-1],
                                    )
                                    all_orders.extend(success_data)
                                fetched_for_exc = True
                                break
                            elif resp.status_code in (401, 403):
                                logger.error(
                                    "ICICI Breeze session token expired or invalid (HTTP %s).",
                                    resp.status_code,
                                )
                                auth_error_encountered = True
                                break
                            else:
                                logger.warning(
                                    "ICICI Breeze %s (%s) HTTP %s: %s",
                                    endpoint_url.split("/")[-1],
                                    exc,
                                    resp.status_code,
                                    resp.text,
                                )
                        except PermissionError:
                            auth_error_encountered = True
                            break
                        except Exception as e_endpoint:
                            logger.debug("Error requesting %s: %s", endpoint_url, e_endpoint)

                    if auth_error_encountered:
                        break

            if auth_error_encountered:
                raise PermissionError("BROKER_TOKEN_EXPIRED")

            logger.info("Successfully fetched %d total records from ICICI Breeze.", len(all_orders))
            return all_orders
        except PermissionError:
            raise
        except Exception as e:
            logger.error("ICICI Breeze fetch_trades error: %s", e, exc_info=True)
            raise


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
                if self.cache_client:
                    try:
                        from app.services.rate_limiter import ProviderRateLimiter

                        ProviderRateLimiter(self.cache_client).check_and_increment(
                            "icici_breeze"
                        )
                    except Exception as rle:
                        logger.debug(f"ICICI Breeze rate limit tracking note: {rle}")
                time.sleep(0.05)  # Rate limit safety
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(url, headers=headers, params=params)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        success_data = res_json.get("Success")
                        if success_data and len(success_data) > 0:
                            quote = success_data[0]
                            lTP = Decimal(
                                str(quote.get("lTP") or quote.get("ltp") or 0)
                            )
                            close = Decimal(
                                str(
                                    quote.get("previous_close")
                                    or quote.get("close")
                                    or lTP
                                )
                            )
                            if lTP > 0:
                                prices_data[ticker] = {
                                    "current_price": lTP,
                                    "previous_close": close,
                                }
                                if self.cache_client:
                                    self.cache_client.set_json(
                                        cache_key,
                                        {
                                            "current_price": str(lTP),
                                            "previous_close": str(close),
                                        },
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
                                dt_str = (
                                    c.get("datetime", "").split(" ")[0].split("T")[0]
                                )
                                if dt_str:
                                    c_dt = date.fromisoformat(dt_str)
                                    close_px = Decimal(str(c.get("close", 0)))
                                    historical_data[ticker][c_dt] = close_px
            except Exception as e:
                logger.error(
                    f"ICICI Breeze historical prices error for {stock_code}: {e}"
                )

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
        return [
            {
                "ticker_symbol": clean_q,
                "name": clean_q,
                "exchange": "NSE",
                "asset_type": "STOCK",
                "currency": "INR",
            }
        ]
