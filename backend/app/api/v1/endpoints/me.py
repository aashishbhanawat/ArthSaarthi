import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.dependencies import get_current_active_user
from app.db.session import SessionLocal, get_db
from app.services import backup_service

router = APIRouter()


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


def restore_backup_task_wrapper(user_id: str, backup_data: dict):
    """
    Wrapper to get a new DB session for the background task.
    """
    db = SessionLocal()
    try:
        backup_service.restore_backup(db, user_id, backup_data)
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
    This is a background task. The user will be notified upon completion.
    WARNING: This will delete all existing data for the user!
    """
    content = await file.read()
    try:
        backup_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    background_tasks.add_task(
        restore_backup_task_wrapper, current_user.id, backup_data
    )
    return {"message": "Restore process started in the background."}
