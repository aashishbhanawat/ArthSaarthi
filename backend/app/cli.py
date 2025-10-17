import collections
import csv
import io
import json
import pathlib
import re
import uuid
import zipfile
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Type

import requests
import typer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

app = typer.Typer(help="ArthSaarthi CLI for database and utility operations.")

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
        "face_value_col": "FaceValue",
    },
    "BSE": {
        "filename": BSE_MASTER_FILE,
        "ticker_col": "ScripID",
        "name_col": "ScripName",
        "isin_col": "ISINCode",
        "series_col": "Series",
        "face_value_col": "FaceValue",
    },
}

# --- Helper Functions ---


def _classify_asset(
    ticker: str, name: str, series: str, exchange: str, debug: bool = False,
) -> tuple[str | None, Any]:  # Return Any for bond_type to avoid import
    """Maps asset attributes to its asset_type and bond_type."""
    series = series.upper()
    name = name.upper()
    ticker = ticker.upper()

    # 1. Highest Priority: Specific bond patterns that are unambiguous
    if "T-BILL" in name or re.match(r"^\d{2,3}(TB|T|D)\d{4,6}$", ticker):
        return "BOND", "TBILL"

    # 2. Exchange-specific bond logic
    if exchange == "BSE":
        # CG + 4-digit coupon + letter + 4-digit number (e.g., CG1110S9803)
        # High-confidence BSE bond patterns
        if re.match(r"^CG\d{4}[A-Z]\d{4}$", ticker) or re.match(
            r"^GS\d{2}[A-Z]{3}(\d{4}|\d{2})[A-Z]?$", ticker
        ):
            return "BOND", "GOVERNMENT"
        if re.match(r"^SGB[A-Z0-9]+", ticker) or series == "GB":
            return "BOND", "SGB"

        # For BSE, check for name-based keywords for better accuracy, especially for
        # corporate bonds.
        # This is now independent of the ticker pattern.
        bond_keywords = ["%", "NCD", "BOND", "PERP",
                         " SR ", " BD ", "DEBENTURE", "0 ", " 0%"]
        month_keywords = ["JAN", "FEB", "MAR", "APR", "MAY",
                          "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        # Check for 2-digit or 4-digit years in the name
        year_keywords = [str(y) for y in range(15, 100)] + [
            str(y) for y in range(2015, date.today().year + 10)
        ]
        strong_bond_indicators = [
            "%", "NCD", "BOND", "DEBENTURE"] + month_keywords + year_keywords
        stock_exclusions = ["LTD", "LIMITED", "SECURITIES"]

        # If it has bond keywords, it's likely a bond.
        # We only exclude if it has stock keywords AND lacks strong bond indicators.
        has_bond_keywords = any(keyword in name for keyword in (
            bond_keywords + month_keywords + year_keywords))
        is_likely_stock = any(ex in name for ex in stock_exclusions)
        has_strong_bond_indicators = any(
            ind in name for ind in strong_bond_indicators
        )
        if has_bond_keywords and not (
                is_likely_stock and not has_strong_bond_indicators):
            return "BOND", "CORPORATE"

        # Fallback for State Govt bonds on BSE based on name keywords
        govt_keywords = ["STATE", "ELEC BOARD", "POWER CORPORATION"]
        if any(keyword in name for keyword in govt_keywords) and not any(
            ex in name for ex in ["LTD", "LIMITED"]
        ):
            return "BOND", "GOVERNMENT"
    else:  # Default to NSE logic
        # NSE specific series for bonds. These are high-confidence indicators.
        if series == "GB":
            return "BOND", "SGB"
        if series in ("GS", "SG"):
            return "BOND", "GOVERNMENT"
        if series == "TB":
            return "BOND", "TBILL"

        # Corporate bonds on NSE often start with specific letters.
        # This rule is now structured to explicitly EXCLUDE known stock series.
        BOND_PREFIXES = ("N", "Y", "Z", "D", "S", "U", "M")
        STOCK_SERIES_EXCEPTIONS = {"DR", "ST"}
        OTHER_EXCLUSIONS = {"MF", "ME", "SP", "SL", "SI", "SO", "SQ"}
        NUMERIC_EXCEPTIONS = {"24", "25", "47", "50", "57", "60", "65", "71"}

        if series.startswith(BOND_PREFIXES) and series not in STOCK_SERIES_EXCEPTIONS:
            # If it's another known exclusion or a numeric exception, skip it.
            if series in OTHER_EXCLUSIONS or (
                len(series) > 1 and series[1:] in NUMERIC_EXCEPTIONS
            ):
                return None, None
            return "BOND", "CORPORATE"

    # 3. Last fallback: Check for common stock series if no bond patterns matched.
    if series in {"EQ", "BE", "SM", "DR", "A", "B", "T", "M", "C", "ST"}:
        return "STOCK", None
    return None, None  # Default return for unclassified assets


def get_db_session():
    # Local import to prevent circular dependencies at startup
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_and_clean_asset_row(
    row: dict, exchange: str, config: dict, debug: bool, debug_rows_printed: int
) -> tuple[dict | None, int]:
    """Validates and cleans a row from the asset master file."""
    series = row.get(config["series_col"], "").strip().upper()
    ticker = row.get(config["ticker_col"], "")
    name = row.get(config["name_col"], "")
    asset_type, bond_type = _classify_asset(ticker, name, series, exchange)
    if not asset_type:
        if series and debug and debug_rows_printed < 5:
            typer.echo(  # noqa: E501
                f"\n[DEBUG] Skipping {exchange} row due to unclassified Series "
                f"'{series}'.", err=True,
            )
            typer.echo(f"  - Ticker: {ticker}, Name: {name}", err=True)
            debug_rows_printed += 1
        return None, debug_rows_printed

    isin = row.get(config["isin_col"])

    # We need a name and at least one of (ticker or isin) to track an asset.
    if not name or not (ticker or isin):
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

    face_value_str = row.get(config["face_value_col"], "0").strip()
    try:
        face_value = Decimal(face_value_str)
        if face_value <= 0:
            face_value = None
    except Exception:
        face_value = None

    cleaned_data = {
        "isin": isin.strip(),
        "ticker": ticker.strip(),
        "name": name.strip(),
        "asset_type": asset_type,
        "bond_type": bond_type,
        "face_value": face_value,
    }
    return cleaned_data, debug_rows_printed


def _parse_and_seed_exchange_data(
    db: Session,
    reader: csv.DictReader,
    exchange: str,
    existing_isins: set,
    existing_tickers: set,
    existing_composite_keys: set[tuple[str, str, str]],
    schemas: Any,
    debug: bool = False,
) -> tuple[int, int, collections.Counter]:
    """Parses asset data from a CSV reader and seeds the database."""
    # Local import to prevent circular dependencies
    from app import crud
    from app.schemas.bond import BondCreate
    created_count = 0
    skipped_count = 0
    debug_rows_printed = 0 # type: ignore
    config = EXCHANGE_CONFIGS[exchange]
    skipped_series_counts = collections.Counter()

    # The field names in the file might have quotes, let's strip them.
    if reader.fieldnames:
        reader.fieldnames = [field.strip().strip('"') for field in reader.fieldnames]

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

            # Check if asset with this (name, asset_type, currency) already exists
            # This handles the 'uq_asset_name_type_currency' constraint.
            composite_key = (cleaned_data["name"], cleaned_data["asset_type"], "INR")
            if composite_key in existing_composite_keys:
                if debug and debug_rows_printed < 5:
                    typer.echo((
                        f"\n[DEBUG] Skipping {exchange} row due to duplicate "
                        f"composite key: Name: '{cleaned_data['name']}', Type: "
                        f"'{cleaned_data['asset_type']}', Currency: 'INR'."), err=True
                    )
                    debug_rows_printed += 1
                skipped_count += 1
                continue

            asset_data = {
                "name": cleaned_data["name"],
                "ticker_symbol": cleaned_data["ticker"],
                "isin": cleaned_data["isin"],
                "asset_type": cleaned_data["asset_type"],
                "currency": "INR",
                "exchange": exchange,
            }
            try:
                asset_in = schemas.AssetCreate(**asset_data)
                asset = crud.asset.create(db=db, obj_in=asset_in)

                # If it's a bond, create the associated bond record
                if asset.asset_type == "BOND" and cleaned_data["bond_type"]:
                    bond_in = BondCreate(
                        asset_id=asset.id,
                        bond_type=cleaned_data["bond_type"],
                        # Placeholder date, user must enrich this on first transaction
                        maturity_date=date(1970, 1, 1),
                        isin=asset.isin,
                        face_value=cleaned_data.get("face_value"),
                    )
                    crud.bond.create(db=db, obj_in=bond_in)

                created_count += 1
                # Add to sets to prevent duplicates from other files in the same run
                existing_isins.add(cleaned_data["isin"])
                existing_tickers.add(cleaned_data["ticker"])
                existing_composite_keys.add(composite_key) # type: ignore
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
    db: Session, # noqa: E501
    existing_isins: set, # type: ignore
    existing_tickers: set,
    existing_composite_keys: set[tuple[str, str, str]],
    schemas: Any,
    debug: bool = False,
) -> tuple[int, int, collections.Counter]:
    """Reads a CSV file stream and triggers the seeding process."""
    reader = csv.DictReader(file_content)
    created, skipped, skipped_series = _parse_and_seed_exchange_data(
        db, reader, exchange, existing_isins, existing_tickers, # type: ignore
        existing_composite_keys, schemas, debug=debug
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
    # Local import to prevent circular dependencies
    from app import models, schemas

    """
    Downloads and parses the ICICI Direct Security Master file.

    Seeds the assets table in the database with NSE-first priority.
    """
    typer.echo("Starting asset database seeding process...")
    db: Session = next(get_db_session())
    Asset = models.Asset

    try:
        typer.echo("Fetching existing assets from database...")
        existing_isins = {
            r[0] for r in db.query(Asset.isin).filter(Asset.isin.isnot(None)).all()
        }
        existing_tickers = {r[0] for r in db.query(Asset.ticker_symbol).all()}
        existing_composite_keys = {
            (a.name, a.asset_type, a.currency)
            for a in db.query(Asset.name, Asset.asset_type, Asset.currency).all()
        }
        typer.echo(
            f"Found {len(existing_isins)} existing ISINs and"
            f" {len(existing_tickers)} tickers and"
            f" {len(existing_composite_keys)} composite keys."
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
                        f, exchange, db, existing_isins, existing_tickers,
                        existing_composite_keys, schemas, debug=debug
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
                            text_stream, exchange, db, existing_isins, existing_tickers,
                            existing_composite_keys, schemas, debug=debug
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
        if "UndefinedTable" in str(e):
            typer.secho(
                "\nHint: The database tables do not seem to exist. "
                "Try running 'init-db' first.",
                fg=typer.colors.YELLOW, err=True
            )


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
    from app import models
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
    from app import models
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
    from app.cache.factory import get_cache_client

    typer.echo("Clearing application cache...")
    try:
        cache_client = get_cache_client()
        if hasattr(cache_client, "clear"):
            cache_client.clear()
            typer.secho("Cache cleared successfully.", fg=typer.colors.GREEN)
        else:
            typer.secho(
                "The configured cache client does not support clearing.",
                fg=typer.colors.RED, err=True
            )
    except Exception as e:
        typer.secho(f"An error occurred while clearing cache: {e}",
                    fg=typer.colors.RED,
                    err=True)


if __name__ == "__main__":
    app()
