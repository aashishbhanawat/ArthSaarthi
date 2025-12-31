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
