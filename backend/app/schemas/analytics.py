from pydantic import BaseModel


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

    # xirr: float
    realized_xirr: float
    unrealized_xirr: float


class FixedDepositAnalytics(BaseModel):
    """
    Response model for single fixed deposit analytics.
    """
    unrealized_xirr: float
    realized_xirr: float
