from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
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
