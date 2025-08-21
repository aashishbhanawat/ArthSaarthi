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
    from app.core.config import settings

    # This function should only be run in sqlite mode, which is set by the Electron process
    if settings.DATABASE_TYPE == "sqlite":
        db_path_str = settings.DATABASE_URL.split("///")[1]

        if not os.path.exists(db_path_str):
            print(f"--- Database not found at {db_path_str}, initializing new database... ---")
            # We can use the main executable with the 'db' commands
            subprocess.run([sys.executable, "db", "init-db"], check=True)
            print("--- Database initialization complete. ---")

        print("--- Seeding initial asset data ---")
        try:
            # We also run the seeder as a separate process to ensure it's fresh
            subprocess.run([sys.executable, "db", "seed-assets"], check=True)
            print("--- Asset seeding complete ---")
        except Exception as e:
            print(f"--- Asset seeding failed: {e} ---")

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
