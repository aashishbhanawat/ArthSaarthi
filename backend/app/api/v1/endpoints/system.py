"""
System endpoints for desktop app operations like seeding status.
"""
import logging
import subprocess
import sys
import threading
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class SeedingStatus(str, Enum):
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    NEEDS_SEEDING = "needs_seeding"


class SeedingStatusResponse(BaseModel):
    status: SeedingStatus
    progress: int = 0
    message: str = ""
    asset_count: int = 0
    error: Optional[str] = None


# Global state for seeding progress tracking
# In desktop mode, this is shared across requests
_seeding_state = {
    "status": SeedingStatus.IDLE,
    "progress": 0,
    "message": "",
    "error": None,
    "seeding_started": False,
}


# Minimum asset count to consider seeding complete
MIN_ASSETS_FOR_COMPLETE = 100


def _run_seeding_subprocess():
    """Run seeding as a subprocess."""
    global _seeding_state
    
    try:
        _seeding_state["status"] = SeedingStatus.IN_PROGRESS
        _seeding_state["progress"] = 10
        _seeding_state["message"] = "Starting asset seeding..."
        
        logger.info("Starting background asset seeding subprocess...")
        
        # Run the seed-assets command
        result = subprocess.run(
            [sys.executable, "db", "seed-assets"],
            capture_output=True,
            text=True,
            cwd=None,  # Use current working directory
        )
        
        if result.returncode == 0:
            _seeding_state["status"] = SeedingStatus.COMPLETE
            _seeding_state["progress"] = 100
            _seeding_state["message"] = "Seeding complete!"
            logger.info("Asset seeding completed successfully.")
        else:
            _seeding_state["status"] = SeedingStatus.FAILED
            _seeding_state["error"] = result.stderr or "Seeding failed"
            _seeding_state["message"] = "Seeding failed"
            logger.error(f"Asset seeding failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Seeding subprocess error: {e}")
        _seeding_state["status"] = SeedingStatus.FAILED
        _seeding_state["error"] = str(e)
        _seeding_state["message"] = "Seeding failed"


@router.get("/seeding-status", response_model=SeedingStatusResponse)
def get_seeding_status(db: Session = Depends(get_db)):
    """
    Get the current status of asset seeding.

    Used by desktop splash screen to determine if seeding is needed
    and to show progress.

    Returns:
        - NEEDS_SEEDING: No assets or very few assets in DB
        - IN_PROGRESS: Seeding is currently running
        - COMPLETE: Sufficient assets exist in DB
        - FAILED: Seeding failed (check error field)
    """
    global _seeding_state

    # If seeding is in progress, return current progress with live asset count
    if _seeding_state["status"] == SeedingStatus.IN_PROGRESS:
        try:
            asset_count = db.query(models.Asset).count()
        except Exception:
            asset_count = 0
            
        # Estimate progress based on asset count (target ~40000 assets)
        estimated_progress = min(95, 10 + int((asset_count / 40000) * 85))
        
        return SeedingStatusResponse(
            status=SeedingStatus.IN_PROGRESS,
            progress=estimated_progress,
            message=f"Loading assets... ({asset_count:,} loaded)",
            asset_count=asset_count,
        )

    # If seeding failed, return error
    if _seeding_state["status"] == SeedingStatus.FAILED:
        return SeedingStatusResponse(
            status=SeedingStatus.FAILED,
            progress=0,
            message=_seeding_state["message"],
            error=_seeding_state["error"],
            asset_count=0,
        )

    # Check asset count in database
    try:
        asset_count = db.query(models.Asset).count()

        if asset_count >= MIN_ASSETS_FOR_COMPLETE:
            return SeedingStatusResponse(
                status=SeedingStatus.COMPLETE,
                progress=100,
                message="Asset database ready",
                asset_count=asset_count,
            )
        else:
            return SeedingStatusResponse(
                status=SeedingStatus.NEEDS_SEEDING,
                progress=0,
                message=f"Only {asset_count} assets found. Seeding required.",
                asset_count=asset_count,
            )
    except Exception as e:
        logger.error(f"Error checking asset count: {e}")
        return SeedingStatusResponse(
            status=SeedingStatus.NEEDS_SEEDING,
            progress=0,
            message="Unable to check database",
            asset_count=0,
        )


@router.post("/trigger-seeding")
def trigger_seeding(db: Session = Depends(get_db)):
    """
    Trigger asset seeding process.
    
    Called by Electron splash screen on first run to start seeding
    before user login.
    """
    global _seeding_state
    
    # Don't start if already in progress
    if _seeding_state["seeding_started"]:
        return {"status": "already_started"}
    
    # Check if seeding is actually needed
    try:
        asset_count = db.query(models.Asset).count()
        if asset_count >= MIN_ASSETS_FOR_COMPLETE:
            return {"status": "not_needed", "asset_count": asset_count}
    except Exception:
        pass
    
    # Start seeding in background thread
    _seeding_state["seeding_started"] = True
    _seeding_state["status"] = SeedingStatus.IN_PROGRESS
    _seeding_state["progress"] = 5
    _seeding_state["message"] = "Initializing..."
    
    seed_thread = threading.Thread(target=_run_seeding_subprocess, daemon=True)
    seed_thread.start()
    
    return {"status": "started"}


@router.post("/seeding-progress")
def update_seeding_progress(progress: int, message: str):
    """Update seeding progress (called by backend during seeding)."""
    global _seeding_state
    _seeding_state["status"] = SeedingStatus.IN_PROGRESS
    _seeding_state["progress"] = progress
    _seeding_state["message"] = message
    return {"status": "updated"}


@router.post("/seeding-complete")
def mark_seeding_complete():
    """Mark seeding as complete."""
    global _seeding_state
    _seeding_state["status"] = SeedingStatus.COMPLETE
    _seeding_state["progress"] = 100
    _seeding_state["message"] = "Seeding complete"
    return {"status": "complete"}


@router.post("/seeding-failed")
def mark_seeding_failed(error: str):
    """Mark seeding as failed with error message."""
    global _seeding_state
    _seeding_state["status"] = SeedingStatus.FAILED
    _seeding_state["error"] = error
    _seeding_state["message"] = "Seeding failed"
    return {"status": "failed"}


@router.post("/seeding-reset")
def reset_seeding_status():
    """Reset seeding status to idle (for retry after failure)."""
    global _seeding_state
    _seeding_state = {
        "status": SeedingStatus.IDLE,
        "progress": 0,
        "message": "",
        "error": None,
        "seeding_started": False,
    }
    return {"status": "reset"}
