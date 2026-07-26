from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel

try:
    from pydantic import ConfigDict
except ImportError:
    ConfigDict = None


class DividendEntry(BaseModel):
    transaction_id: str
    asset_name: str
    asset_ticker: str
    date: date
    quantity: Decimal
    amount_native: Decimal
    currency: str
    # TTBR fields (Rule 115 proxy)
    ttbr_date: Optional[date] = None
    ttbr_rate: Optional[Decimal] = None
    amount_inr: Decimal
    period: str

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class DividendSummary(BaseModel):
    fy_year: str
    entries: List[DividendEntry]
    total_amount_inr: Decimal
    bucket_totals: Dict[str, Decimal]

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True
