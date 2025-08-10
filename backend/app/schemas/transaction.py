import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .asset import Asset


# Shared properties
class TransactionBase(BaseModel):
    transaction_type: str
    quantity: Decimal
    price_per_unit: Decimal
    transaction_date: datetime
    fees: Decimal = Decimal("0.0")


# Properties to receive on transaction creation
class TransactionCreate(TransactionBase):
    asset_id: uuid.UUID


# Properties to receive on transaction update
class TransactionUpdate(BaseModel):
    transaction_type: Optional[str] = None
    quantity: Optional[Decimal] = None
    price_per_unit: Optional[Decimal] = None
    transaction_date: Optional[datetime] = None
    fees: Optional[Decimal] = None


# Properties to return to client
class Transaction(TransactionBase):
    id: uuid.UUID
    asset: Asset
    model_config = ConfigDict(from_attributes=True)
