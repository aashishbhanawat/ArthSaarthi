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
    from app.core.config import settings

    if settings.DATABASE_TYPE == 'sqlite':
        from app.db import session, base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # This is still necessary to override the PostgreSQL default
        settings.DATABASE_URL = "sqlite:///./arthsaarthi-desktop.db"
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})
        session.engine = engine
        session.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create tables directly from models if the db file doesn't exist
        db_path = settings.DATABASE_URL.split("///")[1]
        if not os.path.exists(db_path):
            print("--- Database file not found. Creating and initializing. ---")
            base.Base.metadata.create_all(bind=engine)
        else:
            print("--- Database file found. Skipping initialization. ---")

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
