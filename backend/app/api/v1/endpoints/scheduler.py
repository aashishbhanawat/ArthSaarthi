import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_user
from app.core.scheduler import (
    get_scheduler,
    list_jobs,
    pause_job,
    resume_job,
    run_job_now,
)
from app.crud.crud_scheduled_job import scheduled_job_log
from app.db.session import get_db
from app.models.user import User
from app.schemas.scheduler import (
    JobInfo,
    PauseResumeResponse,
    ScheduledJobLogResponse,
    ScheduledJobLogsPaginated,
    SchedulerSummary,
    TriggerJobResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary", response_model=SchedulerSummary)
def get_scheduler_summary(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> SchedulerSummary:
    """
    Fetch consolidated scheduler overview including running state, active/paused counts,
    and failure metrics over the last 24 hours.
    Requires admin privileges.
    """
    scheduler = get_scheduler()
    jobs = list_jobs()

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    failed_count = scheduled_job_log.count_failures_since(db, since=since)

    active_count = sum(1 for j in jobs if j.status in ("ACTIVE", "RUNNING"))
    paused_count = sum(1 for j in jobs if j.status == "PAUSED")

    return SchedulerSummary(
        is_running=scheduler.running,
        total_jobs=len(jobs),
        active_jobs=active_count,
        paused_jobs=paused_count,
        failed_last_24h=failed_count,
        jobs=jobs,
    )


@router.get("/jobs", response_model=list[JobInfo])
def get_scheduled_jobs(
    current_user: User = Depends(get_current_admin_user),
) -> list[JobInfo]:
    """
    List all background jobs registered in the system.
    Requires admin privileges.
    """
    return list_jobs()


@router.post("/jobs/{job_id}/run", response_model=TriggerJobResponse)
def trigger_scheduled_job(
    job_id: str,
    current_user: User = Depends(get_current_admin_user),
) -> TriggerJobResponse:
    """
    Manually triggers immediate execution of a registered background task.
    Requires admin privileges.
    """
    try:
        run_job_now(job_id)
        return TriggerJobResponse(
            message=f"Job '{job_id}' triggered successfully.",
            job_id=job_id,
            status="TRIGGERED",
        )
    except ValueError as e:
        err_msg = str(e)
        if "currently running" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=err_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err_msg,
        )


@router.post("/jobs/{job_id}/pause", response_model=PauseResumeResponse)
def pause_scheduled_job(
    job_id: str,
    current_user: User = Depends(get_current_admin_user),
) -> PauseResumeResponse:
    """
    Pauses scheduled execution of a job.
    Requires admin privileges.
    """
    try:
        pause_job(job_id)
        return PauseResumeResponse(
            message=f"Job '{job_id}' has been paused.",
            job_id=job_id,
            status="PAUSED",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/jobs/{job_id}/resume", response_model=PauseResumeResponse)
def resume_scheduled_job(
    job_id: str,
    current_user: User = Depends(get_current_admin_user),
) -> PauseResumeResponse:
    """
    Resumes scheduled execution of a paused job.
    Requires admin privileges.
    """
    try:
        resume_job(job_id)
        return PauseResumeResponse(
            message=f"Job '{job_id}' has been resumed.",
            job_id=job_id,
            status="RESUMED",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/logs", response_model=ScheduledJobLogsPaginated)
def get_scheduled_job_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    job_id: Optional[str] = Query(None),
    job_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> ScheduledJobLogsPaginated:
    """
    Retrieve paginated execution history logs with optional filtering.
    Requires admin privileges.
    """
    total, items = scheduled_job_log.get_multi(
        db,
        skip=skip,
        limit=limit,
        job_id=job_id,
        status=job_status,
    )
    return ScheduledJobLogsPaginated(
        total=total,
        items=[ScheduledJobLogResponse.model_validate(item) for item in items],
    )


@router.delete("/logs")
def prune_scheduled_job_logs(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Prune execution logs older than a specified number of days (default 30).
    Requires admin privileges.
    """
    deleted_count = scheduled_job_log.prune_older_than(db, days=days)
    return {
        "message": f"Successfully pruned {deleted_count} job execution logs older than {days} days.",
        "deleted_count": deleted_count,
    }
