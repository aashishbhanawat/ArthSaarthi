from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base

from app.db.init_db import _ensure_sqlite_columns_exist

Base = declarative_base()


def test_sqlite_auto_column_addition(monkeypatch):
    """
    Tests that _ensure_sqlite_columns_exist detects missing columns in an existing
    SQLite database table (e.g. goals.expected_return from v1.2.0 upgrade) and adds them
    without throwing errors or truncating data.
    """
    test_engine = create_engine("sqlite:///:memory:")

    # 1. Create a legacy goals table missing expected_return column
    with test_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE goals (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    target_amount NUMERIC(15, 2) NOT NULL,
                    target_date DATE NOT NULL,
                    user_id VARCHAR(36) NOT NULL,
                    created_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO goals (id, name, target_amount, target_date, user_id)
                VALUES ('g1', 'Retirement', 1000000.00, '2040-01-01', 'u1')
                """
            )
        )

    # Verify column is missing initially
    inspector = inspect(test_engine)
    cols = {c["name"] for c in inspector.get_columns("goals")}
    assert "expected_return" not in cols

    # 2. Monkeypatch db_engine and database_type to run auto-migration on test_engine
    monkeypatch.setattr("app.db.init_db.db_engine", test_engine)
    monkeypatch.setattr("app.db.init_db.settings.DATABASE_TYPE", "sqlite")

    _ensure_sqlite_columns_exist()

    # 3. Verify column is added and existing data is intact
    inspector = inspect(test_engine)
    cols_after = {c["name"] for c in inspector.get_columns("goals")}
    assert "expected_return" in cols_after

    with test_engine.begin() as conn:
        query = text("SELECT id, name, expected_return FROM goals WHERE id = 'g1'")
        result = conn.execute(query).fetchone()
        assert result[0] == "g1"
        assert result[1] == "Retirement"
        assert result[2] is None
