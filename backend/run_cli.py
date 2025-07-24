import typer
from app.cli import app as db_cli_app

app = typer.Typer(
    name="pms-cli",
    help="A command-line interface for managing the Personal Portfolio Management System.",
    add_completion=False,
)
app.add_typer(db_cli_app, name="db", help="Commands for database operations like seeding assets.")

if __name__ == "__main__":
    app()