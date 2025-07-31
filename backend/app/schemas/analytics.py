from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    """
    Response model for portfolio analytics data.
    """
    xirr: float
    sharpe_ratio: float
