import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.db import base  # Import the new base file
from app.core.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    db_url = str(settings.DATABASE_URL)
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup, create database tables if not in a test environment
    if os.getenv("TESTING") != "1":
        base.Base.metadata.create_all(bind=engine)
    yield
    # On shutdown (can add cleanup logic here if needed)

app = FastAPI(
    title="Personal Portfolio Management System",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
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