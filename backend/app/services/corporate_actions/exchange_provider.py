import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

import httpx
import yfinance as yf

from app.schemas.stock_corporate_action import RawStockCorporateAction
from app.services.corporate_actions.parser import (
    parse_bse_corporate_action,
    parse_nse_corporate_action,
)

logger = logging.getLogger(__name__)

NSE_HOME_URL = "https://www.nseindia.com"
NSE_CORP_ACTIONS_URL = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"
BSE_CORP_ACTIONS_URL = "https://api.bseindia.com/BseIndiaAPI/api/DefaultData/w"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-actions",
}


def fetch_nse_corporate_actions(
    client: Optional[httpx.Client] = None, timeout: float = 15.0
) -> List[RawStockCorporateAction]:
    """
    Fetches corporate actions from NSE India API.
    Pre-warms the session with nseindia.com to obtain cookies, then queries the corporateActions endpoint.
    """
    actions: List[RawStockCorporateAction] = []
    owns_client = client is None

    try:
        http_client = client or httpx.Client(
            headers=BROWSER_HEADERS, timeout=timeout, follow_redirects=True
        )
        try:
            # 1. Warm-up request to establish session cookies
            logger.info("Initializing NSE session cookies from %s", NSE_HOME_URL)
            http_client.get(NSE_HOME_URL)

            # 2. Fetch corporate actions
            logger.info("Fetching NSE corporate actions from %s", NSE_CORP_ACTIONS_URL)
            response = http_client.get(NSE_CORP_ACTIONS_URL)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        parsed = parse_nse_corporate_action(item)
                        if parsed:
                            actions.append(parsed)
                    logger.info("Successfully fetched %d corporate actions from NSE.", len(actions))
                else:
                    logger.warning("NSE API returned unexpected non-list JSON payload.")
            else:
                logger.warning(
                    "NSE corporate actions endpoint returned status HTTP %d",
                    response.status_code,
                )
        finally:
            if owns_client:
                http_client.close()
    except Exception as e:
        logger.warning("Failed to fetch corporate actions from NSE: %s", e)

    return actions


def fetch_bse_corporate_actions(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    client: Optional[httpx.Client] = None,
    timeout: float = 15.0,
) -> List[RawStockCorporateAction]:
    """
    Fetches corporate actions from BSE India API.
    """
    actions: List[RawStockCorporateAction] = []
    owns_client = client is None

    if from_date is None:
        from_date = date.today() - timedelta(days=30)
    if to_date is None:
        to_date = date.today() + timedelta(days=30)

    params = {
        "Fdate": from_date.strftime("%Y%m%d"),
        "TDate": to_date.strftime("%Y%m%d"),
        "ddlcategorys": "E",
        "segment": "0",
        "strSearch": "S",
    }
    bse_headers = {
        **BROWSER_HEADERS,
        "Referer": "https://www.bseindia.com/corporates/corporate_act.aspx",
        "Origin": "https://www.bseindia.com",
    }

    try:
        http_client = client or httpx.Client(
            headers=bse_headers, timeout=timeout, follow_redirects=True
        )
        try:
            logger.info("Fetching BSE corporate actions from %s with params %s", BSE_CORP_ACTIONS_URL, params)
            response = http_client.get(BSE_CORP_ACTIONS_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        parsed = parse_bse_corporate_action(item)
                        if parsed:
                            actions.append(parsed)
                    logger.info("Successfully fetched %d corporate actions from BSE.", len(actions))
            else:
                logger.warning("BSE API returned status HTTP %d", response.status_code)
        finally:
            if owns_client:
                http_client.close()
    except Exception as e:
        logger.warning("Failed to fetch corporate actions from BSE: %s", e)

    return actions


def fetch_yfinance_corporate_actions(
    ticker_symbol: str, exchange: Optional[str] = None, max_days: int = 90
) -> List[RawStockCorporateAction]:
    """
    Fetches corporate actions for a specific ticker symbol using yfinance.
    Serves as reliable fallback for Indian equities and primary provider for Global/US stocks.
    Restricted to max_days lookback (default 90 days) to prevent retroactively re-applying
    historical splits or dividends that already exist in imported user tradebooks.
    """
    actions: List[RawStockCorporateAction] = []
    upper_ticker = ticker_symbol.upper()
    is_indian_equity = (
        upper_ticker.endswith(".NS")
        or upper_ticker.endswith(".BO")
        or str(exchange).upper() in ("NSE", "BSE", "NSI")
    )

    # Determine yfinance formatted ticker
    if upper_ticker.endswith(".NS") or upper_ticker.endswith(".BO"):
        yf_ticker = upper_ticker
    elif str(exchange).upper() in ("NSE", "NSI"):
        yf_ticker = f"{upper_ticker}.NS"
    elif str(exchange).upper() == "BSE":
        yf_ticker = f"{upper_ticker}.BO"
    else:
        yf_ticker = upper_ticker

    min_date = date.today() - timedelta(days=max_days)

    try:
        ticker = yf.Ticker(yf_ticker)
        actions_df = ticker.actions
        if actions_df is not None and not actions_df.empty:
            for idx, row in actions_df.iterrows():
                # idx is timestamp of the action
                action_date = idx.date() if hasattr(idx, "date") else date.today()
                if action_date < min_date:
                    continue

                # 1. Dividend
                div = row.get("Dividends", 0.0)
                if div and float(div) > 0:
                    actions.append(
                        RawStockCorporateAction(
                            symbol=upper_ticker,
                            action_type="DIVIDEND",
                            ex_date=action_date,
                            dividend_amount=Decimal(str(div)),
                            source="YFINANCE",
                            raw_subject=f"Dividend {div}",
                        )
                    )

                # 2. Stock Split
                # For Indian equities, yfinance collapses bonus share issues into decimal "Stock Splits"
                # (e.g. 1.333333 for 1:3 bonus, 2.0 for 1:1 bonus). True splits and bonus issues for
                # Indian equities must come from official NSE/BSE feeds with explicit corporate action text.
                if is_indian_equity:
                    continue

                split = row.get("Stock Splits", 0.0)
                if split and float(split) > 0:
                    # yfinance represents split ratio as e.g. 5.0 (for 5:1 split) or 0.5 (for reverse split)
                    split_ratio = Decimal(str(split))
                    actions.append(
                        RawStockCorporateAction(
                            symbol=upper_ticker,
                            action_type="SPLIT",
                            ex_date=action_date,
                            ratio_numerator=split_ratio,
                            ratio_denominator=Decimal("1"),
                            source="YFINANCE",
                            raw_subject=f"Stock Split {split_ratio}:1",
                        )
                    )
    except Exception as e:
        logger.warning("Error fetching yfinance corporate actions for %s: %s", yf_ticker, e)

    return actions
