import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

if settings.DATABASE_TYPE == "sqlite":
    engine = create_engine(
        str(settings.DATABASE_URL), connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
        logger.debug("DB Session: Attempting to commit.")
        db.commit()
        logger.debug("DB Session: Commit successful.")
    except Exception:
        logger.error("DB Session: Exception occurred, rolling back.")
        db.rollback()
        raise
    finally:
        logger.debug("DB Session: Closing session.")
        db.close()
