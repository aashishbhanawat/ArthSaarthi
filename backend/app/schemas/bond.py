from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.transaction import TransactionCreate

from .enums import BondType, PaymentFrequency


# Shared properties
class BondBase(BaseModel):
    bond_type: BondType
    face_value: Decimal | None = Field(
        None, description="The face value of the bond (e.g., 1000). Null for SGBs."
    )
    coupon_rate: Decimal | None = Field(
        None,
        description="The annual coupon rate (e.g., 7.5 for 7.5%). Null for T-Bills."
    )
    maturity_date: date
    isin: str | None = Field(
        None, index=True, description="ISIN for market price lookups of tradable bonds."
    )
    payment_frequency: PaymentFrequency | None = Field(None,
        description="For auto-coupon generation."
    )
    first_payment_date: date | None = Field(None,
        description="For auto-coupon generation."
    )


# Properties to receive on item creation
class BondCreate(BondBase):
    asset_id: UUID


# Properties to receive on item creation via the special bond+transaction endpoint
class BondWithTransactionCreate(BaseModel):
    bond_data: BondBase
    transaction_data: TransactionCreate

# Properties to receive on item update
class BondUpdate(BondBase):
    pass


# Properties shared by models stored in DB
class BondInDBBase(BondBase):
    id: UUID
    asset_id: UUID

    class Config:
        from_attributes = True


# Properties to return to client
class Bond(BondInDBBase):
    pass
