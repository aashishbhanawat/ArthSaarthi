from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.scheduler import start_scheduler
from app.crud.crud_scheduled_job import scheduled_job_log
from app.tests.utils.user import create_random_user, get_access_token

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")

API_PREFIX = f"{settings.API_V1_STR}/admin/scheduler"


def _admin_headers(client: TestClient, db: Session) -> dict:
    admin_user, admin_password = create_random_user(db, is_admin=True)
    token = get_access_token(client, admin_user.email, admin_password)
    return {"Authorization": f"Bearer {token}"}


def _user_headers(client: TestClient, db: Session) -> dict:
    regular_user, user_password = create_random_user(db, is_admin=False)
    token = get_access_token(client, regular_user.email, user_password)
    return {"Authorization": f"Bearer {token}"}


def test_scheduler_summary_permissions(client: TestClient, db: Session):
    """Verify non-admin users cannot access scheduler summary."""
    user_headers = _user_headers(client, db)
    resp = client.get(f"{API_PREFIX}/summary", headers=user_headers)
    assert resp.status_code == 403


def test_scheduler_summary_admin(client: TestClient, db: Session):
    """Verify admin user receives consolidated scheduler summary."""
    start_scheduler()
    admin_headers = _admin_headers(client, db)
    resp = client.get(f"{API_PREFIX}/summary", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "is_running" in data
    assert "total_jobs" in data
    assert data["total_jobs"] >= 1
    assert "jobs" in data


def test_get_scheduled_jobs(client: TestClient, db: Session):
    """Verify admin can list all registered jobs."""
    start_scheduler()
    admin_headers = _admin_headers(client, db)
    resp = client.get(f"{API_PREFIX}/jobs", headers=admin_headers)
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) >= 1
    assert any(j["id"] == "daily_portfolio_snapshot" for j in jobs)


def test_trigger_job_endpoint(client: TestClient, db: Session):
    """Verify manual run endpoint triggers job and handles 404 for unknown job."""
    start_scheduler()
    admin_headers = _admin_headers(client, db)

    # 404 on nonexistent job
    resp = client.post(
        f"{API_PREFIX}/jobs/unknown_job_123/run", headers=admin_headers
    )
    assert resp.status_code == 404

    # Trigger real job
    resp = client.post(
        f"{API_PREFIX}/jobs/daily_portfolio_snapshot/run", headers=admin_headers
    )
    assert resp.status_code in (200, 409)


def test_pause_and_resume_endpoints(client: TestClient, db: Session):
    """Verify pause and resume API endpoints update job status."""
    start_scheduler()
    admin_headers = _admin_headers(client, db)

    resp = client.post(
        f"{API_PREFIX}/jobs/daily_portfolio_snapshot/pause",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "PAUSED"

    resp = client.post(
        f"{API_PREFIX}/jobs/daily_portfolio_snapshot/resume",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESUMED"


def test_get_and_prune_logs(client: TestClient, db: Session):
    """Verify log query, filtering, and pruning endpoints."""
    # Seed a test log entry
    scheduled_job_log.create(
        db,
        job_id="test_prune_job",
        job_name="Test Prune Job",
        status="SUCCESS",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        execution_time_seconds=1.2,
    )

    admin_headers = _admin_headers(client, db)
    resp = client.get(
        f"{API_PREFIX}/logs",
        headers=admin_headers,
        params={"job_id": "test_prune_job"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["job_id"] == "test_prune_job"

    # Prune logs
    resp = client.delete(
        f"{API_PREFIX}/logs", headers=admin_headers, params={"days": 1}
    )
    assert resp.status_code == 200
    assert "deleted_count" in resp.json()
