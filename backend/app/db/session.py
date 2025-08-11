from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Check if the database URL is for SQLite
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Add connect_args only for SQLite to handle multi-threading in FastAPI
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
