from pathlib import Path

from app.core.config import _get_or_create_secret_key


def test_secret_key_persistence(tmp_path, monkeypatch):
    """
    Verifies that _get_or_create_secret_key persists a generated SECRET_KEY
    to secret.key and returns the identical key across application restarts.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    fake_data_dir = tmp_path / "platform_data"
    monkeypatch.setattr(
        "platformdirs.user_data_dir",
        lambda appname, appauthor: str(fake_data_dir),
    )

    key1 = _get_or_create_secret_key()
    assert len(key1) > 20
    assert (fake_data_dir / "secret.key").exists()

    # Re-run function (simulating app restart)
    key2 = _get_or_create_secret_key()
    assert key2 == key1
