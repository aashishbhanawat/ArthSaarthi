import logging

from fastapi import APIRouter

from app.core.config import settings

from .endpoints import (
    assets,
    auth,
    dashboard,
    fixed_deposits,
    goals,
    import_sessions,
    me,
    portfolios,
    testing,
    transactions,
    users,
    watchlists,
)

api_router = APIRouter()
logger = logging.getLogger(__name__)

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(me.router, prefix="/users", tags=["users"])
if settings.DEPLOYMENT_MODE != "desktop":
    api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(
    fixed_deposits.router, prefix="/fixed-deposits", tags=["fixed-deposits"]
)
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)

# Conditionally include the testing router only in the test environment
logger.warning(f"Current ENVIRONMENT in api.py: '{settings.ENVIRONMENT}'")
logger.warning(f"CORS confiured: {settings.CORS_ORIGINS}")
if settings.ENVIRONMENT == "test":
    logger.warning("Adding testing route in api.py")
    api_router.include_router(testing.router, prefix="/testing", tags=["testing"])
api_router.include_router(
    import_sessions.router, prefix="/import-sessions", tags=["import-sessions"]
)
