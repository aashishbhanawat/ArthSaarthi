from decimal import Decimal

from pydantic import BaseModel, Field


class PortfolioAnalytics(BaseModel):
    """
    Response model for portfolio analytics data.
    """

    xirr: float
    sharpe_ratio: float


class AssetAnalytics(BaseModel):
    """
    Response model for single asset analytics.
    """

    xirr_current: float = Field(
        ..., description="XIRR for the currently held lots of the asset."
    )
    xirr_historical: float = Field(
        ...,
        description="XIRR for the entire history of the asset, including sold lots.",
    )
    realized_pnl: Decimal = Field(
        default=Decimal("0"),
        description="Realized P&L from sold shares (Capital Gains)",
    )
    dividend_income: Decimal = Field(
        default=Decimal("0"), description="Total dividend/interest income received"
    )


class FixedDepositAnalytics(BaseModel):
    """
    Response model for single fixed deposit analytics.
    """
    unrealized_xirr: float
    realized_xirr: float


class DiversificationSegment(BaseModel):
    """A single segment in a diversification chart."""
    name: str = Field(..., description="Name of the segment (e.g., 'Technology')")
    value: Decimal = Field(..., description="Total value in portfolio currency")
    percentage: float = Field(..., description="Percentage of total portfolio")
    count: int = Field(..., description="Number of holdings in this segment")


class DiversificationResponse(BaseModel):
    """
    Response model for portfolio diversification analysis (FR6.4).
    """
    by_asset_class: list[DiversificationSegment] = Field(
        default_factory=list,
        description="Breakdown by asset class (Equity, Debt, etc.)"
    )
    by_sector: list[DiversificationSegment] = Field(
        default_factory=list,
        description="Breakdown by sector (equities only)"
    )
    by_industry: list[DiversificationSegment] = Field(
        default_factory=list,
        description="Breakdown by industry (equities only)"
    )
    by_market_cap: list[DiversificationSegment] = Field(
        default_factory=list,
        description="Breakdown by market cap (equities only)"
    )
    by_country: list[DiversificationSegment] = Field(
        default_factory=list,
        description="Breakdown by country/geography"
    )
    total_value: Decimal = Field(
        default=Decimal("0"), description="Total portfolio value"
    )


# Capital Gains schemas (FR6.5)
class GainsBreakdown(BaseModel):
    """Breakdown of gains and losses."""
    gains: Decimal = Field(default=Decimal("0"), description="Total gains")
    losses: Decimal = Field(default=Decimal("0"), description="Total losses (negative)")
    net: Decimal = Field(default=Decimal("0"), description="Net gain/loss")


class TermBreakdown(BaseModel):
    """Short-term and long-term breakdown."""
    short_term: GainsBreakdown = Field(
        default_factory=GainsBreakdown,
        description="Holdings held < 12 months"
    )
    long_term: GainsBreakdown = Field(
        default_factory=GainsBreakdown,
        description="Holdings held >= 12 months"
    )
    total: GainsBreakdown = Field(
        default_factory=GainsBreakdown,
        description="Combined total"
    )


class CapitalGainsHolding(BaseModel):
    """Details of a single holding's capital gains."""
    asset_id: str
    asset_name: str
    ticker: str
    first_buy_date: str | None = None
    holding_period_days: int = 0
    term: str = Field(
        ...,
        description="'short_term' or 'long_term'"
    )
    quantity: Decimal
    cost_basis: Decimal
    current_value: Decimal
    unrealized_gain: Decimal


class CapitalGainsResponse(BaseModel):
    """Response model for capital gains analysis (FR6.5)."""
    unrealized: TermBreakdown = Field(
        default_factory=TermBreakdown,
        description="Unrealized gains from current holdings"
    )
    realized: TermBreakdown = Field(
        default_factory=TermBreakdown,
        description="Realized gains from sold holdings"
    )
    holdings_breakdown: list[CapitalGainsHolding] = Field(
        default_factory=list,
        description="Detailed breakdown by holding"
    )
