from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from .asset import Asset, AssetCreate


# Shared properties
class TransactionBase(BaseModel):
    transaction_type: str
    quantity: Decimal
    price_per_unit: Decimal
    fees: Decimal = 0
    transaction_date: datetime


# Properties to receive on transaction creation
class TransactionCreate(TransactionBase):
    portfolio_id: int
    asset_id: Optional[int] = None
    new_asset: Optional[AssetCreate] = None

    @validator('new_asset', always=True)
    def check_asset_provided(cls, v, values):
        if values.get('asset_id') is None and v is None:
            raise ValueError('Either asset_id or new_asset must be provided')
        if values.get('asset_id') is not None and v is not None:
            raise ValueError('Provide either asset_id or new_asset, not both')
        return v


# This schema is for internal use after validation, ensuring asset_id is present
class TransactionCreateInternal(TransactionBase):
    portfolio_id: int
    asset_id: int


# Properties to receive on transaction update
class TransactionUpdate(BaseModel):
    transaction_type: Optional[str] = None
    quantity: Optional[Decimal] = None
    price_per_unit: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    transaction_date: Optional[datetime] = None


# Properties shared by models stored in DB
class TransactionInDBBase(TransactionBase):
    id: int
    portfolio_id: int
    asset_id: int
    user_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Transaction(TransactionInDBBase):
    asset: Asset


# Properties stored in DB
class TransactionInDB(TransactionInDBBase):
    pass