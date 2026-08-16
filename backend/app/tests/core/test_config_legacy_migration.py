from pathlib import Path

from app.core.config import _get_app_dir


def test_legacy_v1_2_0_directory_migration(tmp_path, monkeypatch):
    """
    Tests that if legacy ~/.arthsaarthi/arthsaarthi.db exists from v1.2.0,
    it is automatically copied to the platformdirs user data directory on
    v1.3.0 startup.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    legacy_dir = fake_home / ".arthsaarthi"
    legacy_dir.mkdir()
    legacy_db = legacy_dir / "arthsaarthi.db"
    legacy_db.write_text("DUMMY_V1_2_0_DB")

    legacy_uploads = legacy_dir / "uploads"
    legacy_uploads.mkdir()
    (legacy_uploads / "test_statement.pdf").write_text("DUMMY_PDF_CONTENT")

    legacy_key = legacy_dir / "master.key"
    legacy_key.write_text("DUMMY_KEY")

    fake_data_dir = tmp_path / "platform_data"
    monkeypatch.setattr(
        "platformdirs.user_data_dir",
        lambda appname, appauthor: str(fake_data_dir),
    )

    app_dir = _get_app_dir()

    assert app_dir == fake_data_dir
    assert (fake_data_dir / "arthsaarthi.db").read_text() == "DUMMY_V1_2_0_DB"
    assert (
        fake_data_dir / "uploads" / "test_statement.pdf"
    ).read_text() == "DUMMY_PDF_CONTENT"
    assert (fake_data_dir / "master.key").read_text() == "DUMMY_KEY"
