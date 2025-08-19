import typer
import uvicorn
print("--- Loading run_cli.py (v2) ---")

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
    if os.getenv("DEPLOYMENT_MODE") == "desktop":
        print("--- DESKTOP MODE DETECTED ---")
        from app.core.config import settings
        from app.db import session
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        print("--- Forcing disk cache and SQLite database ---")
        settings.CACHE_TYPE = "disk"
        settings.DATABASE_URL = "sqlite:///./arthsaarthi-desktop.db"

        # Re-initialize the database engine and session
        print("--- Re-initializing database engine ---")
        session.engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})
        session.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=session.engine)
        print("--- Database engine re-initialized ---")

        # Run database migrations
        print("--- Running database migrations ---")
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
        print("--- Database migrations complete ---")

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
