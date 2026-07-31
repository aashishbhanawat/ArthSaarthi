"""
Metadata service for Upstox integration.
Handles downloading & caching of instrument master files (NSE.json.gz) and market holidays.
"""
import gzip
import json
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional, Set
import urllib.request

from app.cache.base import CacheClient

logger = logging.getLogger(__name__)

NSE_INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
MARKET_HOLIDAYS_URL = "https://api.upstox.com/v2/market/holidays"

CACHE_TTL_HOLIDAYS = 86400  # 24 hours
CACHE_TTL_INSTRUMENTS = 86400  # 24 hours


class UpstoxMetadataService:
    def __init__(self, cache_client: Optional[CacheClient] = None):
        self.cache_client = cache_client
        self._isin_to_key_map: Dict[str, str] = {}
        self._symbol_to_isin_map: Dict[str, str] = {}
        self._symbol_to_key_map: Dict[str, str] = {}
        self._holidays: Set[date] = set()
        self._loaded = False

    def load_metadata_if_needed(self) -> None:
        """Loads instrument maps and holiday lists if not already in memory."""
        if self._loaded:
            return

        self._load_market_holidays()
        self._load_instrument_master()
        self._loaded = True

    def _load_market_holidays(self) -> None:
        """Fetches market holidays from Upstox public API."""
        cache_key = "upstox:market_holidays"
        if self.cache_client:
            cached_data = self.cache_client.get_json(cache_key)
            if cached_data:
                logger.debug("Upstox market holidays cache HIT")
                self._holidays = {date.fromisoformat(d) for d in cached_data}
                return

        try:
            req = urllib.request.Request(
                MARKET_HOLIDAYS_URL,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("status") == "success":
                    holiday_dates = set()
                    for item in data.get("data", []):
                        if item.get("holiday_type") in ("TRADING_HOLIDAY", "SETTLEMENT_HOLIDAY"):
                            date_str = item.get("date")
                            if date_str:
                                holiday_dates.add(date.fromisoformat(date_str))

                    self._holidays = holiday_dates
                    logger.info(f"Loaded {len(self._holidays)} market holidays from Upstox API")

                    if self.cache_client:
                        iso_dates = [d.isoformat() for d in holiday_dates]
                        self.cache_client.set_json(cache_key, iso_dates, expire=CACHE_TTL_HOLIDAYS)
        except Exception as e:
            logger.warning(f"Failed to fetch market holidays from Upstox: {e}")

    def _load_instrument_master(self) -> None:
        """Downloads and parses NSE.json.gz from Upstox CDN to map ISINs & symbols."""
        cache_key = "upstox:instrument_maps"
        if self.cache_client:
            cached_maps = self.cache_client.get_json(cache_key)
            if cached_maps:
                logger.debug("Upstox instrument master cache HIT")
                self._isin_to_key_map = cached_maps.get("isin_to_key", {})
                self._symbol_to_isin_map = cached_maps.get("symbol_to_isin", {})
                self._symbol_to_key_map = cached_maps.get("symbol_to_key", {})
                return

        try:
            req = urllib.request.Request(
                NSE_INSTRUMENTS_URL,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                compressed_data = response.read()
                decompressed_data = gzip.decompress(compressed_data)
                instruments = json.loads(decompressed_data.decode("utf-8"))

                isin_to_key = {}
                symbol_to_isin = {}
                symbol_to_key = {}

                for inst in instruments:
                    segment = inst.get("segment")
                    isin = inst.get("isin")
                    trading_symbol = inst.get("trading_symbol")
                    instrument_key = inst.get("instrument_key")

                    if segment == "NSE_EQ" and instrument_key:
                        if isin:
                            isin_to_key[isin.upper()] = instrument_key
                        if trading_symbol:
                            symbol = trading_symbol.upper()
                            symbol_to_key[symbol] = instrument_key
                            if isin:
                                symbol_to_isin[symbol] = isin.upper()

                self._isin_to_key_map = isin_to_key
                self._symbol_to_isin_map = symbol_to_isin
                self._symbol_to_key_map = symbol_to_key

                logger.info(
                    f"Loaded Upstox instrument master: {len(isin_to_key)} ISINs, "
                    f"{len(symbol_to_key)} Symbols."
                )

                if self.cache_client:
                    self.cache_client.set_json(
                        cache_key,
                        {
                            "isin_to_key": isin_to_key,
                            "symbol_to_isin": symbol_to_isin,
                            "symbol_to_key": symbol_to_key,
                        },
                        expire=CACHE_TTL_INSTRUMENTS,
                    )
        except Exception as e:
            logger.warning(f"Failed to fetch/parse Upstox NSE instrument master: {e}")

    def is_market_closed(self, check_date: date) -> bool:
        """
        Returns True if check_date is a weekend or an official trading holiday.
        """
        self.load_metadata_if_needed()
        # Weekend check (Saturday = 5, Sunday = 6)
        if check_date.weekday() in (5, 6):
            return True
        return check_date in self._holidays

    def get_instrument_key(self, ticker_symbol: str, isin: Optional[str] = None) -> Optional[str]:
        """
        Resolves an Upstox instrument key for a given ticker or ISIN.
        Example outputs:
        - Equity: "NSE_EQ|INE002A01018"
        - Index: "NSE_INDEX|Nifty 50"
        """
        self.load_metadata_if_needed()

        # Handle index tickers
        index_map = {
            "^NSEI": "NSE_INDEX|Nifty 50",
            "^BSESN": "BSE_INDEX|SENSEX",
            "^NSEBANK": "NSE_INDEX|Nifty Bank",
            "INDIAVIX": "NSE_INDEX|India VIX",
        }
        upper_ticker = ticker_symbol.upper().replace(".NS", "").replace(".BO", "")
        if upper_ticker in index_map:
            return index_map[upper_ticker]

        # Try ISIN lookup first
        if isin and isin.upper() in self._isin_to_key_map:
            return self._isin_to_key_map[isin.upper()]

        # Try ticker symbol lookup
        if upper_ticker in self._symbol_to_key_map:
            return self._symbol_to_key_map[upper_ticker]

        # Direct construction fallback if ticker is already an ISIN (starts with INE/INF/IN)
        if upper_ticker.startswith("IN"):
            return f"NSE_EQ|{upper_ticker}"

        return None
