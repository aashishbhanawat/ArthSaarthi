import collections
import csv
import io
import json
import pathlib
import uuid
import zipfile
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Type

import requests
import typer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db.session import SessionLocal
from app.models.asset import Asset
from app.models.asset_alias import AssetAlias
from app.models.audit_log import AuditLog
from app.models.fixed_deposit import FixedDeposit
from app.models.goal import Goal, GoalLink
from app.models.historical_interest_rate import HistoricalInterestRate
from app.models.import_session import ImportSession
from app.models.parsed_transaction import ParsedTransaction
from app.models.portfolio import Portfolio
from app.models.recurring_deposit import RecurringDeposit
from app.models.transaction import Transaction
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem

app = typer.Typer(help="Database commands.")

SECURITY_MASTER_URL = (
    "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
)
NSE_MASTER_FILE = "NSEScripMaster.txt"
BSE_MASTER_FILE = "BSEScripMaster.txt"

EXCHANGE_CONFIGS = {
    "NSE": {
        "filename": NSE_MASTER_FILE,
        "ticker_col": "ExchangeCode",
        "name_col": "CompanyName",
        "isin_col": "ISINCode",
        "series_col": "Series",
        # Filter for equity-like series
        "series_filter": lambda s: s in ("EQ", "BE", "SM"),
    },
    "BSE": {
        "filename": BSE_MASTER_FILE,
        "ticker_col": "ScripID",
        "name_col": "CompanyName",
        "isin_col": "ISINCode",
        "series_col": "Series",
        # Exclude known non-equity series
        "series_filter": lambda s: s not in ("DR", "F", "G"),
    },
}

# --- Helper Functions ---


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_and_clean_asset_row(
    row: dict, exchange: str, config: dict, debug: bool, debug_rows_printed: int
) -> tuple[dict | None, int]:
    """Validates and cleans a row from the asset master file."""
    series = row.get(config["series_col"], "").strip()
    if not config["series_filter"](series):
        if series and debug and debug_rows_printed < 5:
            typer.echo(
                f"\n[DEBUG] Skipping {exchange} row due to Series '{series}'.",
                err=True,
            )
            debug_rows_printed += 1
        return None, debug_rows_printed

    ticker = row.get(config["ticker_col"])
    name = row.get(config["name_col"])
    isin = row.get(config["isin_col"])

    if not all([ticker, name, isin]):
        if debug and debug_rows_printed < 5:
            typer.echo(
                (
                    f"\n[DEBUG] Skipping {exchange} row due to missing"
                    f" essential data. Ticker: '{ticker}', Name: '{name}',"
                    f" ISIN: '{isin}'."
                ),
                err=True,
            )
            debug_rows_printed += 1
        return None, debug_rows_printed

    cleaned_data = {
        "isin": isin.strip(), "ticker": ticker.strip(), "name": name.strip()
    }
    return cleaned_data, debug_rows_printed


def _parse_and_seed_exchange_data(
    db: Session,
    reader: csv.DictReader,
    exchange: str,
    existing_isins: set,
    existing_tickers: set,
    debug: bool = False,
) -> tuple[int, int, collections.Counter]:
    """Parses asset data from a CSV reader and seeds the database."""
    created_count = 0
    skipped_count = 0
    debug_rows_printed = 0
    config = EXCHANGE_CONFIGS[exchange]
    skipped_series_counts = collections.Counter()

    assets_to_process = list(reader)
    with typer.progressbar(
        assets_to_process, label=f"Processing {exchange} assets"
    ) as progress:
        for row in progress:
            cleaned_data, debug_rows_printed = _validate_and_clean_asset_row(
                row, exchange, config, debug, debug_rows_printed
            )
            if not cleaned_data:
                series = row.get(config["series_col"], "").strip()
                if series:
                    skipped_series_counts[series] += 1
                continue

            # Check if asset with this ISIN or Ticker already exists
            if (
                cleaned_data["isin"] in existing_isins
                or cleaned_data["ticker"] in existing_tickers
            ):
                skipped_count += 1
                continue

            asset_data = {
                "name": cleaned_data["name"],
                "ticker_symbol": cleaned_data["ticker"],
                "isin": cleaned_data["isin"],
                "asset_type": "STOCK",
                "currency": "INR",
                "exchange": exchange,
            }
            try:
                asset_in = schemas.AssetCreate(**asset_data)
                crud.asset.create(db=db, obj_in=asset_in)
                created_count += 1
                # Add to sets to prevent duplicates from other files in the same run
                existing_isins.add(cleaned_data["isin"])
                existing_tickers.add(cleaned_data["ticker"])
            except IntegrityError:
                db.rollback()
                skipped_count += 1
            except Exception as ex:
                typer.echo(f"\nCould not create asset {asset_data}: {ex}", err=True)
                skipped_count += 1
    return created_count, skipped_count, skipped_series_counts


def _process_asset_file(
    file_content: io.TextIOWrapper,
    exchange: str,
    db: Session,
    existing_isins: set,
    existing_tickers: set,
    debug: bool = False,
) -> tuple[int, int, collections.Counter]:
    """Reads a CSV file stream and triggers the seeding process."""
    reader = csv.DictReader(file_content)
    # The field names in the file might have quotes, let's strip them.
    if reader.fieldnames:
        reader.fieldnames = [field.strip().strip('"') for field in reader.fieldnames]

    created, skipped, skipped_series = _parse_and_seed_exchange_data(
        db, reader, exchange, existing_isins, existing_tickers, debug=debug
    )
    typer.echo(
        f"\n{exchange} processing complete. Created: {created}, Skipped: {skipped}"
    )
    return created, skipped, skipped_series


# --- CLI Command ---


@app.command("seed-assets")
def seed_assets_command(
    url: str = typer.Option(
        SECURITY_MASTER_URL, "--url", help="URL of the security master zip file."
    ),
    local_dir: pathlib.Path = typer.Option(
        None,
        "--local-dir",
        help=(
            "Path to a local directory containing master files (e.g.,"
            " NSEScripMaster.txt). Skips download."
        ),
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable detailed debug logging for skipped rows."
    ),
):
    """
    Downloads and parses the ICICI Direct Security Master file.

    Seeds the assets table in the database with NSE-first priority.
    """
    typer.echo("Starting asset database seeding process...")
    db: Session = next(get_db_session())

    try:
        typer.echo("Fetching existing assets from database...")
        existing_isins = {
            r[0] for r in db.query(Asset.isin).filter(Asset.isin.isnot(None)).all()
        }
        existing_tickers = {r[0] for r in db.query(Asset.ticker_symbol).all()}
        typer.echo(
            f"Found {len(existing_isins)} existing ISINs and"
            f" {len(existing_tickers)} tickers."
        )

        total_created, total_skipped = 0, 0
        total_skipped_series = collections.Counter()

        # Process files from local directory or downloaded zip
        if local_dir:
            typer.echo(f"Processing local files from: {local_dir}")
            for exchange, config in EXCHANGE_CONFIGS.items():
                file_path = local_dir / config["filename"]
                if not file_path.exists():
                    typer.echo(
                        f"Warning: File '{file_path}' not found. Skipping.", err=True
                    )
                    continue
                with open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
                    created, skipped, skipped_series = _process_asset_file(
                        f, exchange, db, existing_isins, existing_tickers, debug=debug
                    )
                    total_created += created
                    total_skipped += skipped
                    total_skipped_series.update(skipped_series)
        else:
            typer.echo(f"Downloading security master file from {url}...")
            response = requests.get(url)
            response.raise_for_status()
            typer.echo("Download complete.")
            typer.echo("Extracting and processing asset files from zip archive...")
            with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
                for exchange, config in EXCHANGE_CONFIGS.items():
                    filename = config["filename"]
                    if filename not in thezip.namelist():
                        typer.echo(
                            f"Warning: '{filename}' not found in archive.", err=True
                        )
                        continue
                    with thezip.open(filename) as thefile:
                        # Decode to a text stream for the CSV reader
                        text_stream = io.TextIOWrapper(
                            thefile, encoding="utf-8", errors="ignore"
                        )
                        created, skipped, skipped_series = _process_asset_file(
                            text_stream,
                            exchange,
                            db,
                            existing_isins,
                            existing_tickers,
                            debug=debug,
                        )
                        total_created += created
                        total_skipped += skipped
                        total_skipped_series.update(skipped_series)

        typer.echo("\n--- Seeding Summary ---")
        typer.echo(f"Total assets created: {total_created}")
        typer.echo(f"Total assets skipped (duplicates): {total_skipped}")

        if total_skipped_series:
            typer.echo("\n--- Skipped Series Summary ---")
            for series, count in sorted(total_skipped_series.items()):
                typer.echo(f"Series '{series}': {count} rows skipped due to filtering")

        typer.echo("-----------------------")
        db.commit()

    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}", err=True)


@app.command("clear-assets")
def clear_assets_command(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force deletion without confirmation.",
    ),
):
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
            ParsedTransaction,
            ImportSession,
            GoalLink,
            WatchlistItem,
            Transaction,
            FixedDeposit,
            RecurringDeposit,
            Goal,
            Watchlist,
            Portfolio,
            Asset,
        ]

        total_deleted = 0
        for model in models_to_delete:
            num_deleted = db.query(model).delete()
            if num_deleted > 0:
                typer.echo(
                    f"Deleted {num_deleted} rows from {model.__tablename__}."
                )
                total_deleted += num_deleted

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
    """Dumps the contents of a specific database table to the console."""
    db: Session = next(get_db_session())
    try:
        # A simple way to map table names to models. This is not exhaustive.
        model_map = {
            "assets": Asset,
            "portfolios": Portfolio,
            "transactions": Transaction,
            "users": User,
            "historical_interest_rates": HistoricalInterestRate,
            "goals": Goal,
            "goal_links": GoalLink,
            "watchlists": Watchlist,
            "watchlist_items": WatchlistItem,
            "fixed_deposits": FixedDeposit,
            "recurring_deposits": RecurringDeposit,
            "import_sessions": ImportSession,
            "parsed_transactions": ParsedTransaction,
            "asset_aliases": AssetAlias,
            "audit_logs": AuditLog,
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


if __name__ == "__main__":
    app()
