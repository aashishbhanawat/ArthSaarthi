import asyncio
from datetime import datetime, timezone
import logging
import traceback
from typing import Dict, List, Optional, Set

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    EVENT_JOB_SUBMITTED,
    JobExecutionEvent,
    JobSubmissionEvent,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.crud.crud_scheduled_job import scheduled_job_log
from app.db.session import SessionLocal
from app.schemas.scheduler import JobInfo
from app.tasks.registry import TaskDefinition, get_task_registry

logger = logging.getLogger(__name__)

# Module-level singletons and state
_scheduler: Optional[AsyncIOScheduler] = None
_running_jobs: Set[str] = set()
_job_start_times: Dict[str, datetime] = {}


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop


def _get_job_name(job_id: str) -> str:
    registry = get_task_registry()
    if job_id in registry:
        return registry[job_id].name
    return job_id.replace("_", " ").title()


def _handle_job_submission(event: JobSubmissionEvent) -> None:
    job_id = event.job_id
    _running_jobs.add(job_id)
    _job_start_times[job_id] = datetime.now(timezone.utc)
    logger.info(f"Background job '{job_id}' submitted and started execution.")


def _handle_job_execution(event: JobExecutionEvent) -> None:
    job_id = event.job_id
    finished_at = datetime.now(timezone.utc)
    started_at = _job_start_times.pop(job_id, finished_at)
    _running_jobs.discard(job_id)

    duration = max(0.0, (finished_at - started_at).total_seconds())
    job_name = _get_job_name(job_id)

    if event.exception:
        status = "FAILED"
        err_msg = "".join(traceback.format_tb(event.traceback))
        err_msg += f"\n{type(event.exception).__name__}: {event.exception}"
        logger.error(
            f"Background job '{job_id}' failed after {duration:.2f}s: {event.exception}"
        )
    else:
        status = "SUCCESS"
        err_msg = None
        logger.info(
            f"Background job '{job_id}' completed successfully in {duration:.2f}s."
        )

    # Persist log in isolated DB session
    db = SessionLocal()
    try:
        scheduled_job_log.create(
            db,
            job_id=job_id,
            job_name=job_name,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            execution_time_seconds=duration,
            error_message=err_msg,
        )
    except Exception as db_err:
        logger.error(
            f"Failed to record scheduled job log for '{job_id}': {db_err}",
            exc_info=True,
        )
    finally:
        db.close()


def _handle_job_missed(event: JobExecutionEvent) -> None:
    job_id = event.job_id
    _running_jobs.discard(job_id)
    job_name = _get_job_name(job_id)
    now = datetime.now(timezone.utc)
    logger.warning(f"Background job '{job_id}' execution was missed.")

    db = SessionLocal()
    try:
        scheduled_job_log.create(
            db,
            job_id=job_id,
            job_name=job_name,
            status="MISSED",
            started_at=now,
            finished_at=now,
            execution_time_seconds=0.0,
            error_message="Job execution window expired before job could run.",
        )
    except Exception as db_err:
        logger.error(
            f"Failed to record missed job log for '{job_id}': {db_err}",
            exc_info=True,
        )
    finally:
        db.close()


def _apscheduler_listener(event) -> None:
    if event.code == EVENT_JOB_SUBMITTED:
        _handle_job_submission(event)
    elif event.code in (EVENT_JOB_EXECUTED, EVENT_JOB_ERROR):
        _handle_job_execution(event)
    elif event.code == EVENT_JOB_MISSED:
        _handle_job_missed(event)


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        loop = _get_or_create_event_loop()
        _scheduler = AsyncIOScheduler(
            event_loop=loop,
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,
            },
        )
        _scheduler.add_listener(
            _apscheduler_listener,
            EVENT_JOB_SUBMITTED
            | EVENT_JOB_EXECUTED
            | EVENT_JOB_ERROR
            | EVENT_JOB_MISSED,
        )
    return _scheduler


def start_scheduler() -> None:
    """
    Initializes and starts the APScheduler with all registered system tasks.
    """
    loop = _get_or_create_event_loop()
    scheduler = get_scheduler()
    if scheduler._eventloop is None or scheduler._eventloop.is_closed():
        scheduler._eventloop = loop

    if scheduler.running:
        logger.info("APScheduler is already running.")
        return

    registry = get_task_registry()
    for task_id, task_def in registry.items():
        existing_job = scheduler.get_job(task_id)
        if not existing_job:
            scheduler.add_job(
                task_def.func,
                trigger=task_def.trigger,
                id=task_def.job_id,
                name=task_def.name,
                replace_existing=True,
            )
            logger.info(
                f"Registered background job '{task_def.job_id}' with trigger: {task_def.trigger}"
            )

    scheduler.start()
    logger.info("APScheduler started successfully.")


def shutdown_scheduler(wait: bool = False) -> None:
    """
    Gracefully shuts down the background job scheduler.
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        logger.info("Shutting down APScheduler...")
        _scheduler.shutdown(wait=wait)
        logger.info("APScheduler stopped.")
    _scheduler = None


def list_jobs() -> List[JobInfo]:
    """
    Lists all registered background jobs, their triggers, and current statuses.
    """
    scheduler = get_scheduler()
    registry = get_task_registry()
    result: List[JobInfo] = []

    for job_id, task_def in registry.items():
        job = scheduler.get_job(job_id) if scheduler.running else None
        next_run = job.next_run_time if job else None

        if job_id in _running_jobs:
            status = "RUNNING"
        elif job and job.next_run_time is None:
            status = "PAUSED"
        elif job:
            status = "ACTIVE"
        else:
            status = "IDLE"

        trigger_repr = str(job.trigger) if job else str(task_def.trigger)

        result.append(
            JobInfo(
                id=task_def.job_id,
                name=task_def.name,
                trigger=trigger_repr,
                next_run_time=next_run,
                status=status,
                description=task_def.description,
            )
        )

    return result


async def _run_manual_wrapper(task_def: TaskDefinition) -> None:
    job_id = task_def.job_id
    job_name = task_def.name
    started_at = datetime.now(timezone.utc)
    _running_jobs.add(job_id)
    _job_start_times[job_id] = started_at

    status = "SUCCESS"
    err_msg = None
    try:
        await task_def.func()
    except Exception as e:
        status = "FAILED"
        err_msg = "".join(traceback.format_exc())
        logger.error(
            f"Manual run of background job '{job_id}' failed: {e}",
            exc_info=True,
        )
    finally:
        finished_at = datetime.now(timezone.utc)
        duration = max(0.0, (finished_at - started_at).total_seconds())
        _running_jobs.discard(job_id)
        _job_start_times.pop(job_id, None)

        db = SessionLocal()
        try:
            scheduled_job_log.create(
                db,
                job_id=job_id,
                job_name=job_name,
                status=status,
                started_at=started_at,
                finished_at=finished_at,
                execution_time_seconds=duration,
                error_message=err_msg,
            )
        except Exception as db_err:
            logger.error(
                f"Failed to record manual run log for '{job_id}': {db_err}",
                exc_info=True,
            )
        finally:
            db.close()


def run_job_now(job_id: str) -> None:
    """
    Manually dispatches immediate execution of a registered job.
    Raises ValueError if job is not found or is currently executing.
    """
    registry = get_task_registry()
    if job_id not in registry:
        raise ValueError(f"Job '{job_id}' is not registered in the system.")

    if job_id in _running_jobs:
        raise ValueError(f"Job '{job_id}' is currently running.")

    task_def = registry[job_id]
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_run_manual_wrapper(task_def))
    except RuntimeError:
        loop = _get_or_create_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(_run_manual_wrapper(task_def), loop)
        else:
            loop.run_until_complete(_run_manual_wrapper(task_def))


def pause_job(job_id: str) -> None:
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)
    if not job:
        raise ValueError(f"Job '{job_id}' not found in active scheduler.")
    job.pause()


def resume_job(job_id: str) -> None:
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)
    if not job:
        raise ValueError(f"Job '{job_id}' not found in active scheduler.")
    job.resume()
