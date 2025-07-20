from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.financial_data_service import FinancialDataService
from app.core.config import settings
from app import crud


def get_dashboard_summary(db: Session, *, user: User) -> DashboardSummary:
    """
    Calculate and return a summary for the user's dashboard.
    """
    financial_data_service = FinancialDataService(
        api_key=settings.FINANCIAL_API_KEY, api_url=settings.FINANCIAL_API_URL
    )

    portfolios = crud.portfolio.get_multi_by_owner(db=db, user_id=user.id)
    if not portfolios:
        return DashboardSummary(
            total_value=Decimal("0.0"),
            total_unrealized_pnl=Decimal("0.0"),
            total_realized_pnl=Decimal("0.0"),
            top_movers=[],
        )

    total_value = Decimal("0.0")
    for portfolio in portfolios:
        for transaction in portfolio.transactions:
            try:
                price_info = financial_data_service.get_asset_price(
                    transaction.asset.ticker_symbol
                )
                current_price = Decimal(str(price_info.get("price", 0)))
            except Exception:
                current_price = Decimal("0.0")
            total_value += transaction.quantity * current_price

    return DashboardSummary(
        total_value=total_value,
        total_unrealized_pnl=Decimal("0.0"), # Placeholder
        total_realized_pnl=Decimal("0.0"), # Placeholder
        top_movers=[],  # Placeholder
    )


class CRUDDashboard:
    def get_dashboard_summary(self, db: Session, *, user: User) -> DashboardSummary:
        return get_dashboard_summary(db=db, user=user)


dashboard = CRUDDashboard()