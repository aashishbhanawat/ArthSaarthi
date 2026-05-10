import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator

try:
    from pydantic import ConfigDict
    def model_validator(pre=False):
        return root_validator(pre=pre, skip_on_failure=True)
except (ImportError, TypeError):
    ConfigDict = None
    def model_validator(pre=False):
        return root_validator(pre=pre)

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
    details: Optional[Dict[str, Any]] = None

    @model_validator(pre=False)
    @classmethod
    def check_future_date(cls, values: dict) -> dict:
        from datetime import datetime, timezone
        transaction_date = values.get("transaction_date")
        if transaction_date:
            now = datetime.now(timezone.utc)
            target_date = transaction_date
            if isinstance(target_date, str):
                target_date = datetime.fromisoformat(target_date)

            # Ensure we're comparing aware datetimes
            if target_date.tzinfo is None:
                target_date = target_date.replace(tzinfo=timezone.utc)

            if target_date > now:
                raise ValueError("Transaction date cannot be in the future")
        return values


class TransactionLinkCreate(BaseModel):
    buy_transaction_id: uuid.UUID
    quantity: Decimal


# Properties to receive on transaction creation
class TransactionCreate(TransactionBase):
    asset_id: uuid.UUID
    links: Optional[List[TransactionLinkCreate]] = None


# Flexible input schema for the create_transaction endpoint
class TransactionCreateIn(TransactionBase):
    asset_id: Optional[uuid.UUID] = None
    ticker_symbol: Optional[str] = None
    asset_type: Optional[str] = None
    links: Optional[List[TransactionLinkCreate]] = None

    @model_validator(pre=False)
    @classmethod
    def check_asset_provided(cls, values: dict) -> dict:
        if values.get("asset_id") is None and values.get("ticker_symbol") is None:
            raise ValueError("Either asset_id or ticker_symbol must be provided")
        return values

    @model_validator(pre=False)
    @classmethod
    def check_integer_quantities_for_corporate_actions(cls, values: dict) -> dict:
        transaction_type = values.get("transaction_type")
        quantity = values.get("quantity")
        price_per_unit = values.get("price_per_unit")
        if transaction_type in [TransactionType.BONUS, TransactionType.SPLIT]:
            if quantity is not None and quantity % 1 != 0:
                raise ValueError(
                    "Quantity (Ratio New) must be an integer for Bonus/Split."
                )
            if price_per_unit is not None and price_per_unit % 1 != 0:
                raise ValueError(
                    "Price per unit (Ratio Old) must be an integer for Bonus/Split."
                )
        return values


# Properties to receive on transaction update
class TransactionUpdate(TransactionBase):
    transaction_type: Optional[TransactionType] = None  # type: ignore
    quantity: Optional[Decimal] = None
    price_per_unit: Optional[Decimal] = None
    transaction_date: Optional[datetime] = None
    fees: Optional[Decimal] = None
    asset_id: Optional[uuid.UUID] = None
    details: Optional[Dict[str, Any]] = None
    links: Optional[List[TransactionLinkCreate]] = None


# Properties to return to client
class TransactionLink(BaseModel):
    id: uuid.UUID
    sell_transaction_id: uuid.UUID
    buy_transaction_id: uuid.UUID
    quantity: Decimal
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            from_orm = True


class Transaction(TransactionBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    asset: "Asset"
    sell_links: List[TransactionLink] = []  # Include links for accurate lot tracking
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            from_orm = True



class TransactionsResponse(BaseModel):
    transactions: List[Transaction]
    total: int


class TransactionCreatedResponse(BaseModel):
    created_transactions: List[Transaction]
