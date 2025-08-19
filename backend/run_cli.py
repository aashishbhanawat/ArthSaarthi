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
    if os.getenv("DEPLOYMENT_MODE") == "desktop":
        from app.core.config import settings
        settings.CACHE_TYPE = "disk"
        settings.DATABASE_URL = "sqlite:///./arthsaarthi-desktop.db"
    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
