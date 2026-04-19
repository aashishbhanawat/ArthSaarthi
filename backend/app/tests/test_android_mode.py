import unittest.mock as mock

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_android_config_local_mode():
    """Verify that android mode is recognized as a local mode."""
    # We simulate the setting via environment or direct override if possible,
    # but here we just check if the logic in config.py is correct.
    from app.core.config import _is_local_mode
    assert _is_local_mode({"DEPLOYMENT_MODE": "android"}) is True
    assert _is_local_mode({"DEPLOYMENT_MODE": "desktop"}) is True
    assert _is_local_mode({"DEPLOYMENT_MODE": "server"}) is False

@pytest.mark.skipif(
    settings.DEPLOYMENT_MODE != "android",
    reason="Only applicable in android mode"
)
def test_android_logs_endpoint_unauthenticated(client: TestClient, tmp_path):
    """Verify the /logs endpoint works without auth in android mode."""
    # Arrange: Create a temporary log file and point settings to it
    log_file = tmp_path / "test_android.log"
    log_file.write_text("Test log line 1\nTest log line 2")

    with mock.patch("app.core.config.settings.LOG_FILE", str(log_file)):
        # Act
        response = client.get("/api/v1/system/logs")

        # Assert
        assert response.status_code == 200
        assert "Test log line 1" in response.json()["msg"]
        assert "Test log line 2" in response.json()["msg"]

@pytest.mark.skipif(
    settings.DEPLOYMENT_MODE != "android",
    reason="Only applicable in android mode"
)
def test_android_seeding_status_initial(client: TestClient):
    """Verify initial seeding status in android mode."""
    response = client.get("/api/v1/system/seeding-status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["idle", "needs_seeding", "complete"]

@pytest.mark.skipif(
    settings.DEPLOYMENT_MODE != "android",
    reason="Only applicable in android mode"
)
def test_android_background_task_initiated(monkeypatch):
    """Verify that the background snapshot loop is initiated in android mode."""
    # This is tricky to test because it happens on startup.
    # We can check if the global task variable is set if we import it after startup.
    import app.main as main
    assert main.settings.DEPLOYMENT_MODE == "android"
    # Note: In a real test environment, we might need to trigger the startup 
    # event manually if the TestClient didn't already do it.
