import os

from app.core.config import settings


def get_db_type():
    if os.getenv("FORCE_SQLITE_TEST", "false").lower() == "true":
        return "sqlite"
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql"):
        return "postgresql"
    return "sqlite"
