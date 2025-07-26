from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal
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
    asset_id: int

# Properties to receive on transaction update
class TransactionUpdate(BaseModel):
    pass


# Properties to return to client
class Transaction(TransactionBase):
    id: int
    asset: Asset
    model_config = ConfigDict(from_attributes=True)