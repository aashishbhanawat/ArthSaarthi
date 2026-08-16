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


def test_legacy_v1_2_0_migration_overwrites_blank_new_db(tmp_path, monkeypatch):
    """
    Tests that if a blank 0-user new_db was created by an initial v1.3.0 boot,
    _get_app_dir still replaces it with legacy_db if legacy_db contains user accounts.
    """
    import sqlite3

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # 1. Create legacy DB with 1 user
    legacy_dir = fake_home / ".arthsaarthi"
    legacy_dir.mkdir()
    legacy_db = legacy_dir / "arthsaarthi.db"
    conn_leg = sqlite3.connect(str(legacy_db))
    conn_leg.execute("CREATE TABLE users (id INT)")
    conn_leg.execute("INSERT INTO users VALUES (1)")
    conn_leg.commit()
    conn_leg.close()

    # 2. Create blank new DB with 0 users
    fake_data_dir = tmp_path / "platform_data"
    fake_data_dir.mkdir()
    new_db = fake_data_dir / "arthsaarthi.db"
    conn_new = sqlite3.connect(str(new_db))
    conn_new.execute("CREATE TABLE users (id INT)")
    conn_new.commit()
    conn_new.close()

    monkeypatch.setattr(
        "platformdirs.user_data_dir",
        lambda appname, appauthor: str(fake_data_dir),
    )

    app_dir = _get_app_dir()
    assert app_dir == fake_data_dir

    # Verify that new_db was replaced by legacy_db (now has 1 user)
    conn_result = sqlite3.connect(str(new_db))
    cur = conn_result.cursor()
    cur.execute("SELECT count(*) FROM users")
    count = cur.fetchone()[0]
    conn_result.close()
    assert count == 1

