import logging
from alembic import command
from alembic.config import Config

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core import config
from app.core import dependencies as deps
from app.db.base import Base  # Import Base with all models registered
from app.db.session import engine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reset-db", status_code=status.HTTP_204_NO_CONTENT)
def reset_db(
    db: Session = Depends(deps.get_db),
) -> Response:
    """
    Resets the database to a clean state for E2E testing.

    This endpoint is database-aware. For SQLite, it drops and recreates all tables
    directly from the models to avoid Alembic's limited support for ALTER TABLE.
    For PostgreSQL, it uses the standard Alembic downgrade/upgrade cycle.

    This endpoint is only available in a test environment and will raise a
    403 Forbidden error otherwise.
    """
    if config.settings.ENVIRONMENT != "test":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in the test environment.",
        )

    logger.info(f"E2E: Resetting database (Type: {config.settings.DATABASE_TYPE})...")

    if config.settings.DATABASE_TYPE == "sqlite":
        # For SQLite, Alembic downgrades can fail due to limited ALTER TABLE support.
        # A more robust reset is to drop and recreate all tables directly from the models.
        logger.info("E2E: Using drop/create all for SQLite.")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        # After recreating, we need to stamp it again so the next test run doesn't fail.
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        logger.info("E2E: SQLite database reset and stamped successfully.")
    else:
        # For PostgreSQL, using Alembic is the correct way to ensure a clean schema.
        logger.info("E2E: Using alembic downgrade/upgrade for PostgreSQL.")
        try:
            alembic_cfg = Config("alembic.ini")
            command.downgrade(alembic_cfg, "base")
            command.upgrade(alembic_cfg, "head")
            logger.info("E2E: Database reset via Alembic successful.")
        except Exception as e:
            logger.error(f"E2E: Alembic command failed: {e}", exc_info=True)
            # Re-raise as an HTTPException to provide feedback to the test runner
            raise HTTPException(status_code=500, detail=f"Alembic command failed: {e}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
