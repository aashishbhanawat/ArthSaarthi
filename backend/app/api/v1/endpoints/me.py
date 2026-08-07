import json
import logging
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.dependencies import get_current_active_user
from app.db.session import SessionLocal, get_db
from app.services import backup_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """Get current user."""
    return current_user


@router.get("/me/backup")
def backup_user_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Generate and download a backup of the user's data.
    """
    data = backup_service.create_backup(db, current_user.id)
    filename = f"arthsaarthi_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


async def restore_backup_task_wrapper(user_id: str, file_content: bytes):
    """
    Wrapper to run the blocking restore operation in a thread pool.
    """
    db = SessionLocal()
    try:

        def _parse_and_restore():
            try:
                backup_data = json.loads(file_content)
                backup_service.restore_backup(db, user_id, backup_data)
            except json.JSONDecodeError:
                logger.error(
                    f"Invalid JSON file uploaded for user {user_id} during restore."
                )
            except Exception as e:
                logger.error(
                    f"An error occurred during the restore process for user {user_id}: {e}"
                )

        await run_in_threadpool(_parse_and_restore)
    finally:
        db.close()


@router.post("/me/restore")
async def restore_user_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Restore user data from a backup file.
    This is an asynchronous background task.
    WARNING: This will delete all existing data for the user!
    """
    content = await file.read()
    background_tasks.add_task(restore_backup_task_wrapper, current_user.id, content)
    return {"message": "Restore process started in the background."}
