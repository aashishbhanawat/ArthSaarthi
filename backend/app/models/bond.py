import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.schemas.enums import BondType, PaymentFrequency

if TYPE_CHECKING:
    from .asset import Asset  # noqa: F401


class Bond(Base):
    __tablename__ = "bonds"

    id: Mapped[uuid.UUID] = mapped_column("id", primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id"), unique=True, nullable=False)
    bond_type: Mapped[BondType] = mapped_column(String, nullable=False)
    face_value: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    coupon_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    payment_frequency: Mapped[Optional[PaymentFrequency]] = mapped_column(
        String, nullable=True)
    first_payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="bond")
