from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RawStockCorporateAction(BaseModel):
    """
    Normalized representation of a corporate action fetched from an exchange
    (NSE, BSE) or market provider (yfinance).
    """
    symbol: str
    action_type: str = Field(..., description="DIVIDEND, SPLIT, or BONUS")
    ex_date: date
    record_date: Optional[date] = None
    dividend_amount: Optional[Decimal] = None
    ratio_numerator: Optional[Decimal] = None
    ratio_denominator: Optional[Decimal] = None
    source: str = Field("NSE", description="Data source identifier: NSE, BSE, YFINANCE")
    raw_subject: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
