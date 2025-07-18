from fastapi import APIRouter

from .endpoints import auth, users, portfolios, assets, transactions

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])