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
    import subprocess
    import sys
    import threading
    from urllib.parse import urlparse

    from app.core.config import settings

    # This command is for the desktop app, so we assume DEPLOYMENT_MODE is 'desktop'
    # The environment variable is set by the Electron process that calls this.
    if settings.DEPLOYMENT_MODE == "desktop":
        # Use urlparse to robustly get the path from the database URL
        parsed_url = urlparse(settings.DATABASE_URL)
        db_path_str = parsed_url.path.lstrip('/')

        is_first_run = not os.path.exists(db_path_str)

        if is_first_run:
            print(f"--- Database not found at {db_path_str}, "
                  "initializing new database... ---")
            subprocess.run([sys.executable, "db", "init-db"], check=True)
            print("--- Database initialization complete. ---")
            print("--- Skipping asset seeding on first run (complete setup first) ---")
        else:
            # Only seed in background on subsequent runs (database already exists)
            # This avoids database locking issues during first-time user setup
            def seed_in_background():
                import time
                # Wait a bit for server to stabilize
                time.sleep(5)
                print("--- Starting background asset seeding ---")
                try:
                    subprocess.run([sys.executable, "db", "seed-assets"], check=True)
                    print("--- Asset seeding complete ---")
                except Exception as e:
                    print(f"--- Asset seeding failed: {e} ---")

            seed_thread = threading.Thread(target=seed_in_background, daemon=True)
            seed_thread.start()

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
