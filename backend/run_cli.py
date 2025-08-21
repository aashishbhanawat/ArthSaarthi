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


@app.command("run-dev-server")
def run_dev_server(
    host: str = typer.Option("127.0.0.1", help="The host to bind the server to."),
    port: int = typer.Option(8000, help="The port to run the server on."),
):
    """
    Starts the Uvicorn server for development and for the Electron app.
    """
    import os
    from app.core.config import settings

    # For desktop mode, we need to ensure a consistent setup
    os.environ['DATABASE_TYPE'] = 'sqlite'
    from app.core.config import settings # Re-import settings after setting env var
    import sys
    import subprocess
    from pathlib import Path

    # Use a stable directory in the user's home for the database
    app_dir = Path.home() / ".arthsaarthi"
    app_dir.mkdir(exist_ok=True)
    db_path = app_dir / "arthsaarthi.db" # Use the unified name from config

    # Manually override the settings to ensure all parts of the app use the correct path
    settings.DATABASE_URL = f"sqlite:///{db_path.resolve()}"

    from app.db import session, base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})
    session.engine = engine
    session.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # The environment for subprocesses must also know it's in sqlite mode
    subprocess_env = {**os.environ, "DATABASE_TYPE": "sqlite"}

    if not db_path.exists():
        print(f"--- Database not found at {db_path}, initializing new database... ---")
        subprocess.run(
            [sys.executable, "-m", "app.cli", "db", "init-db"],
            check=True,
            env=subprocess_env,
        )
        print("--- Database initialization complete. ---")

    print("--- Seeding initial asset data ---")
    try:
        subprocess.run(
            [sys.executable, "-m", "app.cli", "db", "seed-assets"],
            check=True,
            env=subprocess_env,
        )
        print("--- Asset seeding complete ---")
    except Exception as e:
        print(f"--- Asset seeding failed: {e} ---")

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
