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
    from urllib.parse import urlparse

    from app.core.config import settings

    # This command is for the desktop app, so we assume DEPLOYMENT_MODE is 'desktop'
    # The environment variable is set by the Electron process that calls this.
    if settings.DEPLOYMENT_MODE == "desktop":
        print("=== [DEBUG] Desktop mode detected ===")
        print(f"=== [DEBUG] DATABASE_URL: {settings.DATABASE_URL} ===")

        # Use urlparse to robustly get the path from the database URL
        # SQLite URLs are like sqlite:////home/user/.arthsaarthi/arthsaarthi.db
        # urlparse gives path as ///home/... so we need to extract the absolute path
        parsed_url = urlparse(settings.DATABASE_URL)
        raw_path = parsed_url.path
        print(f"=== [DEBUG] Parsed raw_path: '{raw_path}' ===")

        # For sqlite:////path, path is "///path" - we want "/path"
        # Remove the extra slashes but keep one leading slash for absolute path
        if raw_path.startswith('///'):
            db_path_str = raw_path[2:]  # ///home -> /home
            print(f"=== [DEBUG] Stripped '///' to: '{db_path_str}' ===")
        elif raw_path.startswith('//'):
            db_path_str = raw_path[1:]  # //home -> /home
            print(f"=== [DEBUG] Stripped '//' to: '{db_path_str}' ===")
        else:
            db_path_str = raw_path
            print(f"=== [DEBUG] Path unchanged: '{db_path_str}' ===")

        print(f"--- Checking database path: {db_path_str} ---")
        is_first_run = not os.path.exists(db_path_str)
        exists = os.path.exists(db_path_str)
        print(f"=== [DEBUG] os.path.exists: {exists} ===")
        print(f"=== [DEBUG] is_first_run: {is_first_run} ===")

        if is_first_run:
            print(f"--- Database not found at {db_path_str}, "
                  "initializing new database... ---")
            subprocess.run([sys.executable, "db", "init-db"], check=True)
            print("--- Database initialization complete. ---")
            # Note: Asset seeding is now triggered by the splash screen
            # via the /api/v1/system/trigger-seeding endpoint
        else:
            # For existing databases, run any necessary schema migrations
            # This handles the upgrade path for adding new columns
            print("--- Checking for database schema updates... ---")
            run_sqlite_migrations(db_path_str)
            print("--- Schema update check complete. ---")

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
