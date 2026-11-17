import logging
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.schemas.stock_corporate_action import RawStockCorporateAction

logger = logging.getLogger(__name__)

# Month name mapping for NSE date strings like "14-Nov-2026" or "14-NOV-2026"
NSE_DATE_FORMATS = ["%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y", "%Y-%m-%d"]
BSE_DATE_FORMATS = ["%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%Y-%m-%d"]


def parse_date_safe(date_str: Any, formats: List[str]) -> Optional[date]:
    """Attempts to parse a date string using a list of possible date formats."""
    if not date_str or not isinstance(date_str, str):
        if isinstance(date_str, (date, datetime)):
            return date_str.date() if isinstance(date_str, datetime) else date_str
        return None

    cleaned = date_str.strip()
    if not cleaned or cleaned.upper() in ("-", "NA", "N/A", "NULL"):
        return None

    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def parse_action_details(subject: str) -> tuple[Optional[str], Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
    """
    Parses the free-text subject/purpose into (action_type, dividend_amount, ratio_numerator, ratio_denominator).
    Supports:
    1. Dividends (Interim, Final, Special, e.g. "Dividend - Rs 10 Per Share", "Re 1 Per Share")
    2. Stock Splits (e.g. "Face Value Split From Rs 10/- To Rs 2/-", "Split 10 to 1")
    3. Bonus Issues (e.g. "Bonus 1:1", "Bonus 1:2", "Bonus Issue 2:1")
    """
    if not subject:
        return None, None, None, None

    text = subject.strip()
    upper_text = text.upper()

    # 1. Check for Bonus Issue: "Bonus 1:1", "Bonus 1:2", "Bonus 2:1", "Bonus Issue In Ratio Of 1:1"
    bonus_match = re.search(r"BONUS[\s\S]*?(\d+)\s*[:/]\s*(\d+)", upper_text)
    if bonus_match:
        new_shares = Decimal(bonus_match.group(1))
        existing_shares = Decimal(bonus_match.group(2))
        return "BONUS", None, new_shares, existing_shares

    # 2. Check for Stock Split:
    # Pattern A: "Face Value Split From Rs 10/- To Rs 2/-" or "From Rs. 10 to Rs. 1"
    split_fv_match = re.search(
        r"(?:SPLIT|SUB[\s-]?DIVISION)[\s\S]*?(?:RS\.?|INR|RE\.?)?\s*(\d+(?:\.\d+)?)[\s\S]*?TO[\s\S]*?(?:RS\.?|INR|RE\.?)?\s*(\d+(?:\.\d+)?)",
        upper_text,
    )
    if split_fv_match:
        old_fv = Decimal(split_fv_match.group(1))
        new_fv = Decimal(split_fv_match.group(2))
        if new_fv > 0:
            # E.g. 10 to 2 means 5 new shares for 1 old share
            ratio = old_fv / new_fv
            return "SPLIT", None, ratio, Decimal("1")

    # Pattern B: "Split 5:1" or "Split 2 for 1"
    split_ratio_match = re.search(r"SPLIT[\s\S]*?(\d+)\s*(?:[:/]|FOR)\s*(\d+)", upper_text)
    if split_ratio_match:
        new_qty = Decimal(split_ratio_match.group(1))
        old_qty = Decimal(split_ratio_match.group(2))
        if old_qty > 0:
            return "SPLIT", None, new_qty, old_qty

    # 3. Check for Dividend:
    # Pattern: "Dividend - Rs 1.25 Per Share", "Interim Dividend - Rs. 6.00", "Special Dividend - Rs 28", "Re 1"
    if "DIVIDEND" in upper_text or "DIV" in upper_text:
        # Match amount following Rs, Rs., Re, Re., INR, or directly after Dividend
        div_amount_match = re.search(
            r"(?:DIVIDEND|DIV)[\s\S]*?(?:RS\.?|RE\.?|INR)?\s*[-–:]?\s*(\d+(?:\.\d+)?)",
            upper_text,
        )
        if div_amount_match:
            try:
                amount = Decimal(div_amount_match.group(1))
                if amount > 0:
                    return "DIVIDEND", amount, None, None
            except Exception:
                pass

    return None, None, None, None


def parse_nse_corporate_action(item: Dict[str, Any]) -> Optional[RawStockCorporateAction]:
    """
    Parses a single corporate action entry from NSE API JSON payload.
    Expected fields:
      - symbol: "TCS"
      - series: "EQ"
      - subject: "Interim Dividend - Rs 10 Per Share"
      - exDate: "14-Nov-2026"
      - recDate: "15-Nov-2026"
    """
    symbol = str(item.get("symbol", "")).strip().upper()
    if not symbol:
        return None

    # Filter for standard equities (EQ) or BE/BZ series if present
    series = str(item.get("series", "")).strip().upper()
    if series and series not in ("EQ", "BE", "BZ", "SM"):
        return None

    ex_date_str = item.get("exDate")
    ex_date = parse_date_safe(ex_date_str, NSE_DATE_FORMATS)
    if not ex_date:
        return None

    rec_date_str = item.get("recDate")
    rec_date = parse_date_safe(rec_date_str, NSE_DATE_FORMATS)

    subject = str(item.get("subject", "")).strip()
    action_type, div_amt, num, den = parse_action_details(subject)

    if not action_type:
        return None

    return RawStockCorporateAction(
        symbol=symbol,
        action_type=action_type,
        ex_date=ex_date,
        record_date=rec_date,
        dividend_amount=div_amt,
        ratio_numerator=num,
        ratio_denominator=den,
        source="NSE",
        raw_subject=subject,
        raw_data=item,
    )


def parse_bse_corporate_action(
    item: Dict[str, Any], scrip_to_symbol_map: Optional[Dict[str, str]] = None
) -> Optional[RawStockCorporateAction]:
    """
    Parses a single corporate action entry from BSE API JSON payload.
    Expected fields:
      - scrip_code / scripcode: "532540"
      - short_name / Long_Name: "TCS"
      - Purpose: "Interim Dividend - Rs. - 6.0000"
      - Ex_date: "02 Jan 2026"
      - RD_Date: "03 Jan 2026"
    """
    scrip_code = str(item.get("scrip_code") or item.get("scripcode") or "").strip()
    short_name = str(item.get("short_name") or item.get("Long_Name") or "").strip().upper()

    symbol = None
    if scrip_to_symbol_map and scrip_code in scrip_to_symbol_map:
        symbol = scrip_to_symbol_map[scrip_code]
    elif short_name:
        symbol = short_name.split()[0]  # E.g. "TCS LTD" -> "TCS"

    if not symbol:
        return None

    ex_date_str = item.get("Ex_date") or item.get("ex_date")
    ex_date = parse_date_safe(ex_date_str, BSE_DATE_FORMATS)
    if not ex_date:
        return None

    rec_date_str = item.get("RD_Date") or item.get("rd_date")
    rec_date = parse_date_safe(rec_date_str, BSE_DATE_FORMATS)

    purpose = str(item.get("Purpose") or item.get("purpose") or "").strip()
    action_type, div_amt, num, den = parse_action_details(purpose)

    if not action_type:
        return None

    return RawStockCorporateAction(
        symbol=symbol,
        action_type=action_type,
        ex_date=ex_date,
        record_date=rec_date,
        dividend_amount=div_amt,
        ratio_numerator=num,
        ratio_denominator=den,
        source="BSE",
        raw_subject=purpose,
        raw_data=item,
    )
