from app.core.config import settings


def get_db_type():
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql"):
        return "postgresql"
    return "sqlite"
