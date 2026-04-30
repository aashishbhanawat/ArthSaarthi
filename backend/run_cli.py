import typer
import uvicorn

from app.cli import app as db_cli_app
from app.main import app as fastapi_app

app = typer.Typer(
    name="pms-cli",
    help="A CLI for managing the Personal Portfolio Management System.",
    add_completion=False,
)
app.add_typer(
    db_cli_app, name="db", help="Commands for database operations like seeding assets."
)


def run_sqlite_migrations(db_path: str) -> None:
    """
    Runs necessary schema migrations for SQLite databases.
    This is used for upgrading existing desktop installations to new schema versions.
    For new installs, create_all() handles everything.
    """
    import sqlite3

    # List of migrations to run: (table_name, column_name, column_definition)
    # These columns were added in various v1.x releases
    migrations = [
        ("assets", "sector", "TEXT"),
        ("assets", "industry", "TEXT"),
        ("assets", "country", "TEXT"),
        ("assets", "market_cap", "REAL"),
        ("assets", "investment_style", "TEXT"),
        ("assets", "fmv_2018", "REAL"),
    ]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for table_name, column_name, column_def in migrations:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            if column_name not in columns:
                print(f"  Adding column {column_name} to {table_name}...")
                cursor.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
                )
                conn.commit()
                print(f"  Column {column_name} added successfully.")

        conn.close()
    except Exception as e:
        print(f"  Migration warning: {e}")


@app.command("run-dev-server")
def run_dev_server(
    host: str = typer.Option("127.0.0.1", help="The host to bind the server to."),
    port: int = typer.Option(8000, help="The port to run the server on."),
):
    """
    Starts the Uvicorn server for development and for the Electron app.
    """
    import os
    import subprocess
    import sys

    from app.core.config import settings

    # This command is for the desktop app, so we assume DEPLOYMENT_MODE is 'desktop'
    # The environment variable is set by the Electron process that calls this.
    if settings.DEPLOYMENT_MODE == "desktop":
        from app.db.session import engine

        # Use SQLAlchemy's own URL parser to get the DB path.
        # This is the only reliable way to get the correct path on all platforms,
        # including Windows where manual slash stripping produces invalid paths.
        db_path_str = engine.url.database

        is_first_run = not os.path.exists(db_path_str)

        if is_first_run:
            print(f"Initializing new database at {db_path_str}...")
            subprocess.run([sys.executable, "db", "init-db"], check=True)
            print("Database initialization complete.")
            # Note: Asset seeding is now triggered by the splash screen
            # via the /api/v1/system/trigger-seeding endpoint
        else:
            print(f"Upgrading existing database at {db_path_str}...")
            # 1. Create any missing tables that were introduced in newer releases
            from app.db.base import Base
            print("Creating any newly added tables...")
            Base.metadata.create_all(bind=engine)

            # 2. Run manual schema migrations for adding new columns to existing tables
            # This handles the upgrade path for existing Desktop installations
            print("Running manual schema migrations...")
            run_sqlite_migrations(db_path_str)

            # 3. Seed/update historical interest rates (PPF, etc.)
            from app.db.initial_data import seed_interest_rates
            from app.db.session import SessionLocal
            print("Seeding/updating historical interest rates...")
            db = SessionLocal()
            try:
                seed_interest_rates(db)
                db.commit()
            except Exception as e:
                print(f"  Error during interest rate seeding: {e}")
                db.rollback()
            finally:
                db.close()

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
