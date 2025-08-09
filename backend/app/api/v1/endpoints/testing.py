import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.core import config
from app.core import dependencies as deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reset-db", status_code=status.HTTP_204_NO_CONTENT)
def reset_db(
    db: Session = Depends(deps.get_db),
) -> None:
    """
    Resets the database to a clean state for E2E testing.

    This endpoint is only available in a test environment and will raise a
    403 Forbidden error otherwise.
    """

    if config.settings.ENVIRONMENT != "test":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in the test environment.",
        )

    crud.testing.reset_database(db)
    db.commit()
