from fastapi import APIRouter
import logging

from .endpoints import auth, users, portfolios, assets, dashboard, testing
from app.core.config import settings



api_router = APIRouter()
logger = logging.getLogger(__name__)

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Conditionally include the testing router only in the test environment
logger.warning(f"Current ENVIRONMENT in api.py: '{settings.ENVIRONMENT}'")
logger.warning(f"CORS confiured: {settings.CORS_ORIGINS}")
if settings.ENVIRONMENT == 'test':
    logger.warning(f"Adding testing route in api.py")
    api_router.include_router(testing.router, prefix="/testing", tags=["testing"])