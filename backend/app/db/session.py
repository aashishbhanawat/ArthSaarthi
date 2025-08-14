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


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
