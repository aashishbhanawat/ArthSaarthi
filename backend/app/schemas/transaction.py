import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator

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

    @root_validator(pre=False, skip_on_failure=True)
    @classmethod
    def check_future_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        from datetime import datetime, timezone

        transaction_date = values.get("transaction_date")
        if transaction_date:
            now = datetime.now(timezone.utc)
            target_date = transaction_date

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

    @root_validator(pre=False, skip_on_failure=True)
    @classmethod
    def check_asset_provided(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("asset_id") is None and values.get("ticker_symbol") is None:
            raise ValueError("Either asset_id or ticker_symbol must be provided")
        return values

    @root_validator(pre=False, skip_on_failure=True)
    @classmethod
    def check_integer_quantities_for_corporate_actions(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        transaction_type = values.get("transaction_type")
        quantity = values.get("quantity")
        price_per_unit = values.get("price_per_unit")

        if transaction_type in [TransactionType.BONUS, TransactionType.SPLIT]:
            # For these types, quantity and price_per_unit represent ratios
            # and must be integers
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
    class Config:
        from_attributes = True
        orm_mode = True


class Transaction(TransactionBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    asset: "Asset"
    sell_links: List[TransactionLink] = []  # Include links for accurate lot tracking
    class Config:
        from_attributes = True
        orm_mode = True



class TransactionsResponse(BaseModel):
    transactions: List[Transaction]
    total: int


class TransactionCreatedResponse(BaseModel):
    created_transactions: List[Transaction]
