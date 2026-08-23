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


if hasattr(CapitalGainsSummary, "model_rebuild"):
    CapitalGainsSummary.model_rebuild()
else:
    CapitalGainsSummary.update_forward_refs(ForeignGainEntry=ForeignGainEntry)


class UnrealizedTaxLot(BaseModel):
    """Details of an unsold/open tax lot with unrealized gains"""
    holding_id: str
    asset_id: str
    asset_ticker: str
    asset_name: str
    asset_type: str
    buy_date: date
    quantity: Decimal
    buy_price: Decimal
    current_price: Decimal
    total_cost: Decimal
    market_value: Decimal
    unrealized_gain: Decimal
    gain_type: Literal["STCG", "LTCG"]
    holding_days: int
    tax_rate: str
    estimated_tax: Decimal
    is_grandfathered: bool = False
    is_foreign: bool = False
    currency: str = "INR"


class UnrealizedGainsSummary(BaseModel):
    """Summary of unrealized capital gains and Section 112A exemption headroom"""
    financial_year: str
    total_unrealized_stcg: Decimal = Decimal("0.0")
    total_unrealized_ltcg: Decimal = Decimal("0.0")
    total_unrealized_gain: Decimal = Decimal("0.0")
    section_112a_realized_used: Decimal = Decimal("0.0")
    section_112a_remaining_headroom: Decimal = Decimal("0.0")
    section_112a_unrealized_eligible: Decimal = Decimal("0.0")
    section_112a_unrealized_exemption_used: Decimal = Decimal("0.0")
    estimated_unrealized_stcg_tax: Decimal = Decimal("0.0")
    estimated_unrealized_ltcg_tax: Decimal = Decimal("0.0")
    total_estimated_tax: Decimal = Decimal("0.0")
    lots: List[UnrealizedTaxLot] = []


# --- Capital Loss Ledger Schemas ---

class CapitalLossLedgerBase(BaseModel):
    financial_year: str  # e.g., "2023-24"
    assessment_year: str  # e.g., "2024-25"
    stcl_amount: Decimal = Decimal("0.0")
    ltcl_amount: Decimal = Decimal("0.0")
    is_itr_filed_on_time: bool = True
    notes: Optional[str] = None


class CapitalLossLedgerCreate(CapitalLossLedgerBase):
    pass


class CapitalLossLedgerUpdate(BaseModel):
    financial_year: Optional[str] = None
    assessment_year: Optional[str] = None
    stcl_amount: Optional[Decimal] = None
    ltcl_amount: Optional[Decimal] = None
    is_itr_filed_on_time: Optional[bool] = None
    notes: Optional[str] = None


class CapitalLossLedgerResponse(CapitalLossLedgerBase):
    id: str
    user_id: str
    years_remaining: int  # 8-year countdown meter
    is_expired: bool

    class Config:
        from_attributes = True


# --- Net Capital Gains Set-Off Schemas ---

class SetOffBreakdown(BaseModel):
    gross_stcg: Decimal = Decimal("0.0")
    gross_stcl: Decimal = Decimal("0.0")
    gross_ltcg: Decimal = Decimal("0.0")
    gross_ltcl: Decimal = Decimal("0.0")

    # Current Year Intra-Head Set-off
    cy_stcl_offset_against_stcg: Decimal = Decimal("0.0")
    cy_stcl_offset_against_ltcg: Decimal = Decimal("0.0")
    cy_ltcl_offset_against_ltcg: Decimal = Decimal("0.0")

    # Brought-Forward Set-off
    bf_stcl_used: Decimal = Decimal("0.0")
    bf_ltcl_used: Decimal = Decimal("0.0")

    # Net Taxable Gains & Carried Forward Losses
    net_taxable_stcg: Decimal = Decimal("0.0")
    net_taxable_ltcg: Decimal = Decimal("0.0")
    unabsorbed_stcl_to_carry_forward: Decimal = Decimal("0.0")
    unabsorbed_ltcl_to_carry_forward: Decimal = Decimal("0.0")

    # Tax Amounts
    gross_estimated_tax: Decimal = Decimal("0.0")
    net_estimated_tax: Decimal = Decimal("0.0")
    tax_saved_via_setoff: Decimal = Decimal("0.0")


class CapitalSetOffSummaryResponse(BaseModel):
    financial_year: str
    assessment_year: str
    breakdown: SetOffBreakdown
    loss_ledger_entries: List[CapitalLossLedgerResponse] = []


# --- Tax Loss Harvesting Schemas ---

class TaxLossHarvestingItem(BaseModel):
    holding_id: str
    asset_id: str
    asset_ticker: str
    asset_name: str
    asset_type: str
    buy_date: date
    quantity: Decimal
    buy_price: Decimal
    current_price: Decimal
    total_cost: Decimal
    market_value: Decimal
    unrealized_loss: Decimal  # Positive number representing loss amount
    loss_type: Literal["STCL", "LTCL"]
    holding_days: int
    potential_tax_saved: Decimal
    recommended_sell_quantity: Decimal
    recommendation_reason: str


class TaxLossHarvestingSummary(BaseModel):
    financial_year: str
    total_harvestable_stcl: Decimal = Decimal("0.0")
    total_harvestable_ltcl: Decimal = Decimal("0.0")
    total_potential_tax_savings: Decimal = Decimal("0.0")
    net_taxable_stcg_before_harvesting: Decimal = Decimal("0.0")
    net_taxable_ltcg_before_harvesting: Decimal = Decimal("0.0")
    harvesting_opportunities: List[TaxLossHarvestingItem] = []


