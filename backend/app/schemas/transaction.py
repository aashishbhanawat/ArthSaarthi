import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import TransactionType

if TYPE_CHECKING:
    from .asset import Asset  # noqa: F401


# Shared properties
class TransactionBase(BaseModel):
    transaction_type: TransactionType
    quantity: Decimal
    price_per_unit: Decimal
    transaction_date: datetime = Field(
        ..., json_schema_extra={"example": "2023-01-15T12:30:00Z"}
    )
    fees: Decimal = Decimal("0.0")
    details: Optional[dict] = None


# Properties to receive on transaction creation
class TransactionCreate(TransactionBase):
    asset_id: uuid.UUID


# Flexible input schema for the create_transaction endpoint
class TransactionCreateIn(TransactionBase):
    asset_id: Optional[uuid.UUID] = None
    ticker_symbol: Optional[str] = None
    asset_type: Optional[str] = None

    @model_validator(mode="after")
    def check_asset_provided(self) -> "TransactionCreateIn":
        if self.asset_id is None and self.ticker_symbol is None:
            raise ValueError("Either asset_id or ticker_symbol must be provided")
        return self


# Properties to receive on transaction update
class TransactionUpdate(TransactionBase):
    transaction_type: Optional[TransactionType] = None  # type: ignore
    quantity: Optional[Decimal] = None
    price_per_unit: Optional[Decimal] = None
    transaction_date: Optional[datetime] = None
    fees: Optional[Decimal] = None
    asset_id: Optional[uuid.UUID] = None


# Properties to return to client
class Transaction(TransactionBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    asset: "Asset"
    details: Optional[dict] = None
    model_config = ConfigDict(from_attributes=True)


class TransactionsResponse(BaseModel):
    transactions: List[Transaction]
    total: int
