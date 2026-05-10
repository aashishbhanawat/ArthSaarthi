import json
import pathlib
import tempfile
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional, Type

import typer
import urllib3
from sqlalchemy.orm import Session

# Local imports
from app import models
from app.services.asset_seeder import AssetSeeder
from app.utils.financial_utils import (
    process_all_sources,
)

# Suppress only the InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = typer.Typer(help="ArthSaarthi CLI for database and utility operations.")


def get_db_session():
    # Local import to prevent circular dependencies at startup
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _find_file(directory: pathlib.Path, pattern: str) -> Optional[str]:
    """Finds a file matching the pattern in the directory."""
    files = list(directory.glob(pattern))
    if not files:
        return None
    # Return the most recent one if multiple? Or just the first.
    # Let's sort by name (usually contains date) descending.
    files.sort(key=lambda p: p.name, reverse=True)
    return str(files[0])


@app.command("seed-assets")
def seed_assets_command(
    local_dir: pathlib.Path = typer.Option(
        None,
        "--local-dir",
        help=(
            "Path to a local directory containing seed files. "
            "If not provided, attempts to download."
        ),
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable detailed debug logging."
    ),
):
    """
    Seeds the assets table using a multi-phase, authoritative-first strategy.

    Phase 1: Master Debt Lists (NSDL, BSE Public)
    Phase 2: Exchange Bhavcopy (BSE Equity, NSE Equity)
    Phase 3: specialized Debt (NSE Daily, BSE Debt)
    Phase 4: Market Indices (BSE)
    Phase 5: Fallback (ICICI)
    """
    typer.echo("Starting asset database seeding process (V2)...")
    db: Session = next(get_db_session())
    seeder = AssetSeeder(db, debug=debug)

    # Prepare file paths
    files = {}

    if local_dir:
        typer.echo(f"Searching for files in {local_dir}...")
        # Map phases to file patterns
        patterns = {
            "nsdl": ["*nsdl*.xls", "*NSDL*.xls", "*debt_instruments*.xls"],
            "bse_public": [
                "*bonds_data.zip", "*Public Bond*.zip", "bse_public_debt.zip"
            ],
            "bse_equity": ["*BhavCopy_BSE_CM*.csv", "bse_equity.csv"],
            "bse_debt": ["*DEBTBHAVCOPY*.zip", "bse_debt.zip"],
            "nse_debt": ["*New_debt_listing*.xlsx", "nse_daily_debt.xlsx"],
            "nse_equity": ["*BhavCopy_NSE_CM*.csv.zip", "*bhav.csv.zip"],
            "bse_index": ["*INDEXSummary*.csv", "bse_index.csv"],
            "icici": ["*SecurityMaster*.zip", "icici_master.zip"]
        }

        for key, pat_list in patterns.items():
            for pat in pat_list:
                found = _find_file(local_dir, pat)
                if found:
                    files[key] = found
                    break
    else:
        # Download mode
        temp_dir = tempfile.mkdtemp()
        typer.echo(f"Created temp directory for downloads: {temp_dir}")

        try:
            from app.utils.financial_utils import download_all_sources
            # We wrap the download in a way that respects Typer echoes if needed,
            # but download_all_sources handles the logic.
            # For CLI we might want to see the progress, so we pass a logger
            # or just let it run.
            files = download_all_sources(temp_dir)
            if not files:
                typer.echo("Warning: No files were downloaded.")
        except Exception as e:
            typer.echo(f"Error during download setup: {e}", err=True)

    # Execute Phases (consolidated in process_all_sources)
    process_all_sources(seeder, files)

    # Phase 6: Enrichment (FR6.4)

    # Phase 6: Enrichment (FR6.4)
    typer.echo("\n--- Phase 6: Enriching assets with sector/geography data ---")
    enrichment_stats = seeder.enrich_assets(max_assets=50)

    typer.echo("\n--- Seeding Summary ---")
    typer.echo(f"Total assets created: {seeder.created_count}")
    typer.echo(f"Total assets skipped: {seeder.skipped_count}")
    typer.echo(
        f"Enrichment: {enrichment_stats['enriched']} enriched, "
        f"{enrichment_stats['errors']} errors"
    )

    if seeder.skipped_series_counts:
        typer.echo("\n--- Skipped Series Summary (BSE Equity) ---")
        for series, count in sorted(seeder.skipped_series_counts.items()):
            typer.echo(f"Series '{series}': {count} skipped")

    typer.echo("-----------------------")
    seeder.flush_pending()  # Commit any remaining assets

    # Seed/update interest rates (PPF, etc.) every time assets are seeded
    from app.db.initial_data import seed_interest_rates
    typer.echo("\n--- Seeding Interest Rates ---")
    seed_interest_rates(db)

    db.commit()


@app.command("clear-assets")
def clear_assets_command(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force deletion without confirmation.",
    ),
):
    # Local import to prevent circular dependencies
    from app.models.fixed_deposit import FixedDeposit
    from app.models.recurring_deposit import RecurringDeposit
    from app.models.watchlist import Watchlist, WatchlistItem

    """Deletes all portfolio data (transactions, portfolios, assets)."""
    if not force:
        typer.echo(
            "This will permanently delete all assets, transactions, and portfolios"
            " from the database."
        )
        typer.confirm("Are you sure you want to proceed?", abort=True)

    db: Session = next(get_db_session())
    try:
        typer.echo("Deleting all user-generated financial data...")
        # Order is important to respect foreign key constraints
        models_to_delete: list[Type[models.Base]] = [ # type: ignore
            models.ParsedTransaction,
            models.ImportSession,
            models.GoalLink,
            WatchlistItem,
            models.Transaction,
            FixedDeposit,
            RecurringDeposit,
            models.Goal,
            Watchlist,
            models.Portfolio,
            models.Bond,
            models.Asset,
        ]

        total_deleted = 0
        for model in models_to_delete:
            try:
                num_deleted = db.query(model).delete()
                if num_deleted > 0:
                    typer.echo(
                        f"Deleted {num_deleted} rows from {model.__tablename__}."
                    )
                    total_deleted += num_deleted
            except Exception as e:
                # Gracefully handle cases where the table might not exist yet
                typer.echo(f"Could not clear {model.__tablename__}: {e}", err=True)
                db.rollback()
        db.commit()

        if total_deleted > 0:
            typer.secho(
                f"Successfully deleted {total_deleted} records.",
                fg=typer.colors.GREEN,
            )
        else:
            typer.secho("No financial data found to delete.", fg=typer.colors.YELLOW)

    except Exception as e:
        db.rollback()
        typer.secho(f"An error occurred: {e}", fg=typer.colors.RED, err=True)


@app.command("init-db")
def init_db_command(
    create_tables: bool = typer.Option(
        True, help="Create tables from models. Should be false if using Alembic."
    )
):
    # Local import to prevent circular dependencies

    """Initializes the database by creating tables and/or seeding data."""
    db: Session = next(get_db_session())
    from app.db.initial_data import seed_interest_rates

    if create_tables:
        from app.db.base import Base
        from app.db.session import engine
        typer.echo("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        typer.secho("Database tables initialized successfully.", fg=typer.colors.GREEN)

    typer.echo("Seeding initial data...")
    try:
        seed_interest_rates(db)
        db.commit()
        typer.secho("Initial data seeded successfully.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"An error occurred: {e}", fg=typer.colors.RED, err=True)


@app.command("dump-table")
def dump_table_command(
    table_name: str = typer.Argument(..., help="The name of the table to dump."),
):
    # Local import to prevent circular dependencies
    from app.models.audit_log import AuditLog
    from app.models.fixed_deposit import FixedDeposit
    from app.models.recurring_deposit import RecurringDeposit
    from app.models.watchlist import Watchlist, WatchlistItem

    """Dumps the contents of a specific database table to the console."""
    db: Session = next(get_db_session())
    try:
        # A simple way to map table names to models. This is not exhaustive.
        model_map = {
            "assets": models.Asset,
            "portfolios": models.Portfolio,
            "transactions": models.Transaction,
            "users": models.User,
            "historical_interest_rates": models.HistoricalInterestRate,
            "goals": models.Goal,
            "goal_links": models.GoalLink,
            "watchlists": Watchlist,
            "watchlist_items": WatchlistItem,
            "fixed_deposits": FixedDeposit,
            "recurring_deposits": RecurringDeposit,
            "import_sessions": models.ImportSession,
            "parsed_transactions": models.ParsedTransaction,
            "asset_aliases": models.AssetAlias, # type: ignore
            "audit_logs": AuditLog,
            "bonds": models.Bond,
        }
        model = model_map.get(table_name)
        if not model:
            typer.secho(
                f"Error: Table '{table_name}' not found in model map.",
                fg=typer.colors.RED,
            )
            typer.echo("Available tables: " + ", ".join(sorted(model_map.keys())))
            return

        typer.echo(f"--- Dumping contents of table: {table_name} ---")
        records = db.query(model).all()

        if not records:
            typer.secho("Table is empty.", fg=typer.colors.YELLOW)
            return

        def custom_serializer(o: Any) -> str:
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            if isinstance(o, Decimal):
                return f"{o:.2f}"
            if isinstance(o, uuid.UUID):
                return str(o)
            raise TypeError(
                f"Object of type {type(o).__name__} is not JSON serializable"
            )

        for record in records:
            # Remove internal SQLAlchemy state for cleaner output
            record_dict = {
                c.name: getattr(record, c.name) for c in record.__table__.columns
            }
            typer.echo(json.dumps(record_dict, indent=2, default=custom_serializer))

    except Exception as e:
        typer.secho(f"An error occurred: {e}", fg=typer.colors.RED, err=True)


@app.command("clear-cache")
def clear_cache_command():
    """Clears the application cache (Redis or DiskCache)."""
    # Local import to prevent circular dependencies
    from app.cache.factory import get_cache_client, settings

    typer.echo("Clearing application cache...")
    try:
        cache_client = get_cache_client()
        if hasattr(cache_client, "clear"):
            cache_client.clear()
            typer.secho(
                f"Cache of type '{settings.CACHE_TYPE}' cleared successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            typer.secho(
                f"Error: The configured cache client ('{type(cache_client).__name__}') "
                "does not support the 'clear' operation.",
                fg=typer.colors.RED,
                err=True,
            )
    except Exception as e:
        typer.secho(f"An error occurred: {e}", fg=typer.colors.RED, err=True)


if __name__ == "__main__":
    app()
