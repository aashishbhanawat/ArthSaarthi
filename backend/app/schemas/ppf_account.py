from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PpfAccountCreate(BaseModel):
    institution_name: str
    account_number: str | None = None
    opening_date: date
    amount: Decimal
    contribution_date: date
