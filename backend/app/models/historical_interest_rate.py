import uuid

from sqlalchemy import Column, Date, Numeric, String

from app.db.base_class import Base
from app.db.custom_types import GUID


class HistoricalInterestRate(Base):
    __tablename__ = "historical_interest_rates"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    scheme_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)
