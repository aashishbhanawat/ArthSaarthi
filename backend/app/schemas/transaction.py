from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime
from typing import Optional, Any
from decimal import Decimal
from .asset import Asset, AssetCreate


# Shared properties
class TransactionBase(BaseModel):
    transaction_type: str
    quantity: Decimal
    price_per_unit: Decimal
    transaction_date: datetime
    fees: Decimal = Decimal("0.0")


# Properties to receive on transaction creation
class TransactionCreate(TransactionBase):
    asset_id: int | None = None
    new_asset: "AssetCreate | None" = None

    @model_validator(mode='before')
    @classmethod
    def check_asset_info(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get('new_asset') and data.get('asset_id'):
                raise ValueError('Cannot provide both asset_id and new_asset')
            if not data.get('new_asset') and not data.get('asset_id'):
                raise ValueError('Must provide either asset_id or new_asset')
        return data

# Properties to receive on transaction update
class TransactionUpdate(BaseModel):
    fees: Optional[Decimal] = None


# Properties to return to client
class Transaction(TransactionBase):
    id: int
    asset: Asset
    model_config = ConfigDict(from_attributes=True)

from .asset import AssetCreate
TransactionCreate.model_rebuild()