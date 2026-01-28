"""
Schedule FA Schemas for ITR-2/ITR-3 Foreign Assets Reporting
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class ScheduleFAEntry(BaseModel):
    """
    Schedule FA A3 Entry - Foreign Equity and Debt Interest
    Matches ITR-2/ITR-3 Schedule FA format.
    """
    country_code: str
    country_name: str
    entity_name: str  # Name of the company/fund
    entity_address: str = ""
    zip_code: str = ""
    nature_of_entity: str  # "Shares", "Debt Securities", "Units", etc.
    date_acquired: Optional[date]
    initial_value: Decimal  # Value at start of calendar year
    peak_value: Decimal  # Peak value during the year
    peak_value_date: Optional[date] = None  # Date when peak value was reached
    closing_value: Decimal  # Value at end of calendar year (Dec 31)
    gross_amount_received: Decimal  # Dividends/interest during year
    gross_proceeds_from_sale: Decimal  # Sale proceeds during year
    currency: str
    asset_ticker: str
    quantity_held: Decimal


class ScheduleFASummary(BaseModel):
    """Response model for Schedule FA Report"""
    calendar_year: int  # e.g., 2024
    assessment_year: str  # e.g., "2025-26"
    entries: List[ScheduleFAEntry]
    total_initial_value: Decimal = Decimal(0)
    total_peak_value: Decimal = Decimal(0)
    total_closing_value: Decimal = Decimal(0)
    total_gross_proceeds: Decimal = Decimal(0)
