import uuid

from sqlalchemy import Column, Date, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base


class HistoricalInterestRate(Base):
    __tablename__ = "historical_interest_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_name = Column(String, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Null means current/ongoing
    rate = Column(Numeric(precision=5, scale=3), nullable=False)  # e.g., 7.100 for 7.1%

    def __repr__(self):
        return (
            f"<HistoricalInterestRate(scheme_name='{self.scheme_name}', "
            f"start_date='{self.start_date}', end_date='{self.end_date}', "
            f"rate={self.rate})>"
        )
