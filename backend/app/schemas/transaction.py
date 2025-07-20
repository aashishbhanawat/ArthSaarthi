from pydantic import BaseModel, validator
from decimal import Decimal
from datetime import datetime

from .asset import Asset, AssetCreate


# Properties to receive on item creation
class TransactionCreate(BaseModel):
    asset_id: int | None = None
    new_asset: AssetCreate | None = None
    transaction_type: str
    quantity: Decimal
    price_per_unit: Decimal
    fees: Decimal | None = 0.0
    transaction_date: datetime

    @validator('new_asset', always=True)
    def check_asset_info(cls, v, values):
        if v is not None and values.get('asset_id') is not None:
            raise ValueError('Cannot provide both asset_id and new_asset')
        if v is None and values.get('asset_id') is None:
            raise ValueError('Must provide either asset_id or new_asset')
        return v


# Properties to receive on item update
class TransactionUpdate(BaseModel):
    pass  # Not implemented


# Properties shared by models stored in DB
class TransactionInDBBase(BaseModel):
    id: int
    asset_id: int
    portfolio_id: int
    transaction_type: str
    quantity: Decimal
    price_per_unit: Decimal
    fees: Decimal
    transaction_date: datetime
    asset: Asset

    class Config:
        from_attributes = True


# Properties to return to client
class Transaction(TransactionInDBBase):
    pass


# Properties stored in DB
class TransactionInDB(TransactionInDBBase):
    pass