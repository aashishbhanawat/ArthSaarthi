import logging
import subprocess

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core import config
from app.core import dependencies as deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reset-db", status_code=status.HTTP_204_NO_CONTENT)
def reset_db(
    db: Session = Depends(deps.get_db),
) -> Response:
    """
    Resets the database to a clean state for E2E testing by running
    Alembic migrations.

    This endpoint is only available in a test environment and will raise a
    403 Forbidden error otherwise.
    """
    if config.settings.ENVIRONMENT != "test":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in the test environment.",
        )

    logger.info("E2E: Resetting database via Alembic...")
    try:
        # Downgrade to base to drop all tables
        logger.info("E2E: Downgrading database to base...")
        subprocess.run(
            ["alembic", "downgrade", "base"],
            check=True,
            cwd="/app",
            capture_output=True,
        )

        # Upgrade to head to recreate all tables
        logger.info("E2E: Upgrading database to head...")
        subprocess.run(
            ["alembic", "upgrade", "head"], check=True, cwd="/app", capture_output=True
        )
        logger.info("E2E: Database reset via Alembic successful.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except subprocess.CalledProcessError as e:
        logger.error(f"E2E: Alembic command failed: {e.stderr.decode()}")
        raise HTTPException(
            status_code=500, detail=f"Alembic command failed: {e.stderr.decode()}"
        )
