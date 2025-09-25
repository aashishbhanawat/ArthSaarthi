import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, model_validator

# from .asset import Asset  <- This direct import causes the circular dependency


class TransactionType(str):
    BUY = "BUY"
    SELL = "SELL"
    CONTRIBUTION = "CONTRIBUTION"
    INTEREST_CREDIT = "INTEREST_CREDIT"


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
    transaction_type: Optional[str] = None # type: ignore
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
    model_config = ConfigDict(from_attributes=True)


class TransactionsResponse(BaseModel):
    transactions: List[Transaction]
    total: int
