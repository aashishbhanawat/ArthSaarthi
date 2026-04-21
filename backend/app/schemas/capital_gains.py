from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel


class ITRPeriodValues(BaseModel):
    """Stores values for the 5 Advance Tax periods in ITR-2"""
    upto_15_6: Decimal = Decimal("0.0")
    upto_15_9: Decimal = Decimal("0.0")  # 16/6 to 15/9
    upto_15_12: Decimal = Decimal("0.0") # 16/9 to 15/12
    upto_15_3: Decimal = Decimal("0.0")  # 16/12 to 15/3
    upto_31_3: Decimal = Decimal("0.0")  # 16/3 to 31/3


class ITRRow(BaseModel):
    """Represents a row in the ITR-2 Schedule CG Matrix"""
    category_label: str  # e.g., "STCG 20% (Equity)"
    period_values: ITRPeriodValues


class GainEntry(BaseModel):
    """Detailed record of a single realized capital gain transaction"""
    transaction_id: str
    asset_ticker: str
    asset_name: str
    asset_type: str
    buy_date: date
    sell_date: date
    quantity: Decimal
    buy_price: Decimal
    sell_price: Decimal
    total_buy_value: Decimal
    total_sell_value: Decimal
    gain: Decimal
    gain_type: Literal["STCG", "LTCG"]
    holding_days: int
    tax_rate: str # e.g. "12.5%", "Slab"

    # Metadata for warnings
    is_grandfathered: bool = False
    corporate_action_adjusted: bool = False # True if Demerger/Split involved
    is_hybrid_warning: bool = False # Warn user about potential equity/debt ambiguity
    note: Optional[str] = None # Information note (e.g. SGB premature redemption)


class Schedule112AEntry(BaseModel):
    """Row for Schedule 112A (Grandfathered Equity LTCG)"""
    isin: str
    asset_name: str
    quantity: Decimal
    sale_price: Decimal
    full_value_consideration: Decimal
    cost_of_acquisition_orig: Decimal
    fmv_31jan2018: Optional[Decimal]
    total_fmv: Optional[Decimal]
    cost_of_acquisition_final: Decimal # Computed per Sec 55(2)(ac)
    expenditure: Decimal
    total_deductions: Decimal
    balance: Decimal
    acquired_date: date
    transfer_date: date


class CapitalGainsSummary(BaseModel):
    """Response model for Capital Gains Report"""
    financial_year: str
    total_stcg: Decimal
    total_ltcg: Decimal
    estimated_stcg_tax: Decimal
    estimated_ltcg_tax: Decimal

    # Detailed Reports
    itr_schedule_cg: List[ITRRow]
    schedule_112a: List[Schedule112AEntry]
    gains: List[GainEntry]

    # Foreign Capital Gains (in native currency - no INR conversion)
    foreign_gains: List["ForeignGainEntry"] = []


class ForeignGainEntry(BaseModel):
    """
    Capital gain entry for foreign assets.
    Values are in native currency - user/tax consultant must convert using
    SBI TT Buying Rate (Rule 115) for ITR filing.
    """
    transaction_id: str
    asset_ticker: str
    asset_name: str
    asset_type: str
    currency: str  # e.g., "USD", "GBP"
    buy_date: date
    sell_date: date
    quantity: Decimal
    buy_price: Decimal  # In native currency
    sell_price: Decimal  # In native currency
    total_buy_value: Decimal  # In native currency
    total_sell_value: Decimal  # In native currency
    gain: Decimal  # In native currency
    gain_type: Literal["STCG", "LTCG"]
    holding_days: int
    country_code: str = ""  # For Schedule FA reference
