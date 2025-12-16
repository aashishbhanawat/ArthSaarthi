import logging

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_assets,
    admin_interest_rates,
    assets,
    auth,
    dashboard,
    fixed_deposits,
    fx,
    goals,
    import_sessions,
    me,
    portfolios,
    ppf_accounts,
    recurring_deposits,
    testing,
    transactions,
    users,
    watchlists,
)
from app.core.config import settings

api_router = APIRouter()
logger = logging.getLogger(__name__)

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(me.router, prefix="/users", tags=["users"])
if settings.DEPLOYMENT_MODE != "desktop":
    api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(
    ppf_accounts.router, prefix="/ppf-accounts", tags=["ppf-accounts"]
)
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(
    fixed_deposits.router, prefix="/fixed-deposits", tags=["fixed-deposits"]
)
api_router.include_router(
    recurring_deposits.router,
    prefix="/recurring-deposits",
    tags=["recurring-deposits"],
)
api_router.include_router(
    admin_interest_rates.router,
    prefix="/admin/interest-rates",
    tags=["admin-interest-rates"],
)
api_router.include_router(
    admin_assets.router,
    prefix="/admin/assets",
    tags=["admin-assets"],
)
api_router.include_router(fx.router, prefix="/fx-rate", tags=["fx-rate"])

# Conditionally include the testing router only in the test environment
logger.warning(f"Current ENVIRONMENT in api.py: '{settings.ENVIRONMENT}'")
logger.warning(f"CORS confiured: {settings.CORS_ORIGINS}")
if settings.ENVIRONMENT == "test":
    logger.warning("Adding testing route in api.py")
    api_router.include_router(testing.router, prefix="/testing", tags=["testing"])
api_router.include_router(
    import_sessions.router, prefix="/import-sessions", tags=["import-sessions"]
)
