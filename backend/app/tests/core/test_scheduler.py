import asyncio
from datetime import datetime, timezone
import pytest
from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    JobExecutionEvent,
    JobSubmissionEvent,
)
from sqlalchemy.orm import Session

from app.core.scheduler import (
    _apscheduler_listener,
    _handle_job_execution,
    _handle_job_submission,
    _job_start_times,
    _running_jobs,
    get_scheduler,
    list_jobs,
    pause_job,
    resume_job,
    run_job_now,
    shutdown_scheduler,
    start_scheduler,
)
from app.crud.crud_scheduled_job import scheduled_job_log
from app.tasks.registry import TaskDefinition, get_task_registry

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_scheduler_lifecycle():
    """Verify scheduler initializes, starts, and gracefully shuts down."""
    start_scheduler()
    scheduler = get_scheduler()
    assert scheduler.running is True

    # Calling start again when already running is a safe no-op
    start_scheduler()
    assert scheduler.running is True

    # Shutdown
    shutdown_scheduler(wait=False)
    assert get_scheduler().running is False


def test_list_jobs():
    """Verify list_jobs returns all registered tasks with valid triggers."""
    start_scheduler()
    jobs = list_jobs()
    assert len(jobs) >= 1
    snapshot_job = next(
        (j for j in jobs if j.id == "daily_portfolio_snapshot"), None
    )
    assert snapshot_job is not None
    assert snapshot_job.name == "Daily Portfolio Valuation Snapshot"
    assert snapshot_job.status in ("ACTIVE", "RUNNING", "IDLE")
    shutdown_scheduler(wait=False)


def test_job_listeners_record_success_in_db(db: Session):
    """Verify job execution listener records successful runs in DB."""
    job_id = "test_success_job"
    sub_event = JobSubmissionEvent(512, job_id, None, [datetime.now(timezone.utc)])
    _handle_job_submission(sub_event)

    assert job_id in _running_jobs
    assert job_id in _job_start_times

    exec_event = JobExecutionEvent(
        1024, job_id, None, datetime.now(timezone.utc), retval=42
    )
    _handle_job_execution(exec_event)

    assert job_id not in _running_jobs
    assert job_id not in _job_start_times

    total, items = scheduled_job_log.get_multi(db, job_id=job_id)
    assert total >= 1
    assert items[0].status == "SUCCESS"
    assert items[0].execution_time_seconds is not None
    assert items[0].error_message is None


def test_job_listeners_record_failure_in_db(db: Session):
    """Verify job error listener captures exceptions and records traceback."""
    job_id = "test_failing_job"
    sub_event = JobSubmissionEvent(512, job_id, None, [datetime.now(timezone.utc)])
    _handle_job_submission(sub_event)

    err = RuntimeError("Simulated background job failure")
    exec_event = JobExecutionEvent(
        2048, job_id, None, datetime.now(timezone.utc), exception=err, traceback=None
    )
    _handle_job_execution(exec_event)

    assert job_id not in _running_jobs
    total, items = scheduled_job_log.get_multi(db, job_id=job_id)
    assert total >= 1
    assert items[0].status == "FAILED"
    assert "Simulated background job failure" in (items[0].error_message or "")


def test_run_job_now_dispatches_task():
    """Verify run_job_now initiates execution and prevents duplicate concurrent runs."""
    start_scheduler()

    # Simulate an active running job in the concurrency set
    _running_jobs.add("daily_portfolio_snapshot")
    try:
        with pytest.raises(ValueError, match="is currently running"):
            run_job_now("daily_portfolio_snapshot")
    finally:
        _running_jobs.discard("daily_portfolio_snapshot")

    # Invalid job ID
    with pytest.raises(ValueError, match="not registered"):
        run_job_now("non_existent_job_xyz")

    # Test normal manual dispatch
    run_job_now("daily_portfolio_snapshot")
    shutdown_scheduler(wait=False)


def test_pause_and_resume_job():
    """Verify pause and resume functions modify job state in APScheduler."""
    start_scheduler()
    pause_job("daily_portfolio_snapshot")
    scheduler = get_scheduler()
    job = scheduler.get_job("daily_portfolio_snapshot")
    assert job is not None
    assert job.next_run_time is None

    resume_job("daily_portfolio_snapshot")
    assert job.next_run_time is not None

    with pytest.raises(ValueError, match="not found"):
        pause_job("non_existent_job")

    with pytest.raises(ValueError, match="not found"):
        resume_job("non_existent_job")

    shutdown_scheduler(wait=False)
