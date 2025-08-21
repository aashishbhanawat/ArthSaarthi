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
    import sys
    import subprocess

    # For desktop mode, we force the deployment mode to 'desktop'
    # This ensures the correct settings (SQLite, stable DB path) are loaded from config.py
    os.environ['DEPLOYMENT_MODE'] = 'desktop'

    # We need to get the db_path from the settings *after* the env var is set
    from app.core.config import settings
    db_path = settings.DATABASE_URL.split("///")[1]

    # The environment for subprocesses must also know it's in desktop mode
    subprocess_env = {**os.environ, "DEPLOYMENT_MODE": "desktop"}

    if not os.path.exists(db_path):
        print(f"--- Database not found at {db_path}, initializing new database... ---")
        subprocess.run(
            [sys.executable, "db", "init-db"],
            check=True,
            env=subprocess_env,
        )
        print("--- Database initialization complete. ---")

    print("--- Seeding initial asset data ---")
    try:
        subprocess.run(
            [sys.executable, "db", "seed-assets"],
            check=True,
            env=subprocess_env,
        )
        print("--- Asset seeding complete ---")
    except Exception as e:
        print(f"--- Asset seeding failed: {e} ---")

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
