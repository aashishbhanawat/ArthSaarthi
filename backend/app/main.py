from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.db import base  # Import the new base file
from app.core.config import settings
from app.db.session import engine

# Create all tables defined in models that are imported in db.base
# This is suitable for development, for production, a migration tool like Alembic is recommended.
base.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Personal Portfolio Management System",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    # Use the origins from the settings
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")