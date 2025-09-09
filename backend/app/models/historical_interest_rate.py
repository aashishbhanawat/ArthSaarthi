import uuid

from sqlalchemy import Column, Date, Numeric, String, UniqueConstraint

from app.db.base_class import Base
from app.db.custom_types import GUID


class HistoricalInterestRate(Base):
    __tablename__ = "historical_interest_rates"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    scheme_name = Column(String, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rate = Column(Numeric(precision=5, scale=2), nullable=False)
    __table_args__ = (
        UniqueConstraint(
            "scheme_name", "start_date", name="uq_historical_interest_rate_scheme_date"
        ),
    )
