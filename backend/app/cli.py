import json
import os
import pathlib
import tempfile
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, Type, Union

import requests
import typer
from sqlalchemy.orm import Session

# Local imports
from app import models
from app.services.asset_seeder import AssetSeeder

app = typer.Typer(help="ArthSaarthi CLI for database and utility operations.")


def get_db_session():
    # Local import to prevent circular dependencies at startup
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _download_file(url: str, dest_path: str) -> bool:
    """
    Downloads a file from a URL to a destination path.
    Returns True if successful, False otherwise.
    """
    typer.echo(f"Downloading {url}...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        # verify=False for NSDL/Sandbox issues
        response = requests.get(
            url, stream=True, verify=False, headers=headers, timeout=30
        )
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        typer.echo(f"Saved to {dest_path}")
        return True
    except Exception as e:
        typer.echo(f"Download failed: {e}")
        return False


def _find_file(directory: pathlib.Path, pattern: str) -> Optional[str]:
    """Finds a file matching the pattern in the directory."""
    files = list(directory.glob(pattern))
    if not files:
        return None
    # Return the most recent one if multiple? Or just the first.
    # Let's sort by name (usually contains date) descending.
    files.sort(key=lambda p: p.name, reverse=True)
    return str(files[0])


def get_latest_trading_date() -> date:
    """Returns the latest potential trading date (today or previous weekday)."""
    d = date.today()
    # Simple check: if Sat (5) or Sun (6), go back to Fri
    if d.weekday() == 5:  # Sat
        d -= timedelta(days=1)
    elif d.weekday() == 6:  # Sun
        d -= timedelta(days=2)
    return d


def decrement_trading_day(d: date) -> date:
    """Returns the previous trading day (skipping weekends)."""
    d -= timedelta(days=1)
    while d.weekday() > 4:  # Sat=5, Sun=6
        d -= timedelta(days=1)
    return d


def get_dynamic_urls(d: date) -> dict[str, Union[str, list[str]]]:
    """Generates URLs for a specific date."""
    dd = d.strftime("%d")
    mm = d.strftime("%m")
    yyyy = d.strftime("%Y")

    # NSDL: as_on_DD.MM.YYYY.xls
    nsdl = (
        "https://nsdl.co.in/downloadables/excel/cp-debt/"
        f"Download_the_entire_list_of_Debt_Instruments_(including_Redeemed)_as_on_"
        f"{dd}.{mm}.{yyyy}.xls"
    )

    # BSE Equity: BhavCopy_BSE_CM_0_0_0_{YYYY}{MM}{DD}_F_0000.CSV
    bse_eq = (
        "https://www.bseindia.com/download/BhavCopy/Equity/"
        f"BhavCopy_BSE_CM_0_0_0_{yyyy}{mm}{dd}_F_0000.CSV"
    )

    # BSE Debt: DEBTBHAVCOPY{DD}{MM}{YYYY}.zip
    bse_debt = (
        "https://www.bseindia.com/download/Bhavcopy/Debt/"
        f"DEBTBHAVCOPY{dd}{mm}{yyyy}.zip"
    )

    # BSE Index: INDEXSummary_{DD}{MM}{YYYY}.csv
    bse_index = (
        "https://www.bseindia.com/bsedata/Index_Bhavcopy/"
        f"INDEXSummary_{dd}{mm}{yyyy}.csv"
    )

    # NSE Equity: New Uniform Format
    # BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip
    nse_eq = (
        "https://nsearchives.nseindia.com/content/cm/"
        f"BhavCopy_NSE_CM_0_0_0_{yyyy}{mm}{dd}_F_0000.csv.zip"
    )

    # Static URLs (Do not change with date, but we include them)
    bse_public = "https://www.bseindia.com/downloads1/bonds_data.zip"
    nse_debt = "https://nsearchives.nseindia.com/content/debt/New_debt_listing.xlsx"
    icici_fallback = (
        "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
    )

    return {
        "nsdl": nsdl,
        "bse_public": bse_public,
        "bse_equity": bse_eq,
        "bse_debt": bse_debt,
        "nse_debt": nse_debt,
        "nse_equity": nse_eq,
        "bse_index": bse_index,
        "icici": icici_fallback,
    }


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

        # Prepare candidate dates (Today, T-1, T-2)
        candidate_dates = []
        current_d = get_latest_trading_date()
        candidate_dates.append(current_d)
        for _ in range(2):
            current_d = decrement_trading_day(current_d)
            candidate_dates.append(current_d)

        typer.echo(f"Will try dates: {[d.isoformat() for d in candidate_dates]}")

        try:
            required_sources = [
                "nsdl", "bse_public", "bse_equity", "bse_debt",
                "nse_debt", "nse_equity", "bse_index", "icici"
            ]

            for source in required_sources:
                # Try each date for this source
                for d in candidate_dates:
                    urls = get_dynamic_urls(d).get(source)
                    if not urls:
                        continue

                    if isinstance(urls, str):
                        urls = [urls]

                    success = False
                    for url in urls:
                        filename = url.split('/')[-1]
                        dest = os.path.join(temp_dir, filename)

                        if _download_file(url, dest):
                            files[source] = dest
                            success = True
                            break

                    if success:
                        break # Move to next source if successful

                if source not in files:
                    typer.echo(
                        f"Warning: Could not download {source} after trying all dates."
                    )

        except Exception as e:
            typer.echo(f"Error during download setup: {e}", err=True)

    # Execute Phases

    # Phase 1
    if "nsdl" in files:
        seeder.process_nsdl_file(files["nsdl"])
    if "bse_public" in files:
        seeder.process_bse_public_debt(files["bse_public"])

    # Phase 2
    if "bse_equity" in files:
        seeder.process_bse_equity_bhavcopy(files["bse_equity"])
    if "nse_equity" in files:
        seeder.process_nse_equity_bhavcopy(files["nse_equity"])

    # Phase 3
    if "nse_debt" in files:
        seeder.process_nse_daily_debt(files["nse_debt"])
    if "bse_debt" in files:
        seeder.process_bse_debt_bhavcopy(files["bse_debt"])

    # Phase 4
    if "bse_index" in files:
        seeder.process_bse_index(files["bse_index"])

    # Phase 5
    if "icici" in files:
        seeder.process_icici_fallback(files["icici"])

    typer.echo("\n--- Seeding Summary ---")
    typer.echo(f"Total assets created: {seeder.created_count}")
    typer.echo(f"Total assets skipped: {seeder.skipped_count}")

    if seeder.skipped_series_counts:
        typer.echo("\n--- Skipped Series Summary (BSE Equity) ---")
        for series, count in sorted(seeder.skipped_series_counts.items()):
            typer.echo(f"Series '{series}': {count} skipped")

    typer.echo("-----------------------")
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
