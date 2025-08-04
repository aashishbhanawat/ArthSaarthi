import pathlib
import io
import csv
import zipfile
import collections

import requests
import typer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app import crud, schemas
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction

app = typer.Typer(help="Database commands.")

SECURITY_MASTER_URL = "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
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
    MAX_DEBUG_ROWS = 5
    config = EXCHANGE_CONFIGS[exchange]
    skipped_series_counts = collections.Counter()

    assets_to_process = list(reader)
    with typer.progressbar(
        assets_to_process, label=f"Processing {exchange} assets"
    ) as progress:
        for row in progress:
            series = row.get(config["series_col"], "").strip()
            if not config["series_filter"](series):
                if series:
                    skipped_series_counts[series] += 1
                if debug and debug_rows_printed < MAX_DEBUG_ROWS:
                    typer.echo(f"\n[DEBUG] Skipping {exchange} row due to Series '{series}'.", err=True)
                    debug_rows_printed += 1
                continue

            ticker = row.get(config["ticker_col"])
            name = row.get(config["name_col"])
            isin = row.get(config["isin_col"])

            # Skip if essential data is missing
            if not all([ticker, name, isin]):
                if debug and debug_rows_printed < MAX_DEBUG_ROWS:
                    typer.echo(f"\n[DEBUG] Skipping {exchange} row due to missing essential data. Ticker: '{ticker}', Name: '{name}', ISIN: '{isin}'.", err=True)
                    debug_rows_printed += 1
                continue

            # Clean up the values
            isin = isin.strip()
            ticker = ticker.strip()
            name = name.strip()

            if not all([isin, ticker, name]):
                continue

            # Check if asset with this ISIN or Ticker already exists
            if isin in existing_isins or ticker in existing_tickers:
                skipped_count += 1
                continue

            asset_data = {
                "name": name,
                "ticker_symbol": ticker,
                "isin": isin,
                "asset_type": "STOCK",
                "currency": "INR",
                "exchange": exchange,
            }
            try:
                asset_in = schemas.AssetCreate(**asset_data)
                crud.asset.create(db=db, obj_in=asset_in)
                created_count += 1
                # Add to sets to prevent duplicates from other files in the same run
                existing_isins.add(isin)
                existing_tickers.add(ticker)
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
    typer.echo(f"\n{exchange} processing complete. Created: {created}, Skipped: {skipped}")
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
        help="Path to a local directory containing master files (e.g., NSEScripMaster.txt). Skips download.",
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
    Downloads the ICICI Direct Security Master file, parses it, and seeds the assets table
    in the database with NSE-first priority.
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
            f"Found {len(existing_isins)} existing ISINs and {len(existing_tickers)} tickers."
        )

        total_created, total_skipped = 0, 0
        total_skipped_series = collections.Counter()

        # Process files from local directory or downloaded zip
        if local_dir:
            typer.echo(f"Processing local files from: {local_dir}")
            for exchange, config in EXCHANGE_CONFIGS.items():
                file_path = local_dir / config["filename"]
                if not file_path.exists():
                    typer.echo(f"Warning: File '{file_path}' not found. Skipping.", err=True)
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
                        typer.echo(f"Warning: '{filename}' not found in archive.", err=True)
                        continue
                    with thezip.open(filename) as thefile:
                        # Decode to a text stream for the CSV reader
                        text_stream = io.TextIOWrapper(thefile, encoding="utf-8", errors="ignore")
                        created, skipped, skipped_series = _process_asset_file(
                            text_stream, exchange, db, existing_isins, existing_tickers, debug=debug
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
    )
):
    """Deletes all portfolio-related data (transactions, portfolios, assets) from the database."""
    if not force:
        typer.echo(
            "This will permanently delete all assets, transactions, and portfolios from the database."
        )
        typer.confirm("Are you sure you want to proceed?", abort=True)

    db: Session = next(get_db_session())
    try:
        typer.echo("Deleting all transactions, portfolios, and assets...")
        num_transactions_deleted = db.query(Transaction).delete()
        num_portfolios_deleted = db.query(Portfolio).delete()
        num_assets_deleted = db.query(Asset).delete()
        db.commit()
        typer.secho(f"Successfully deleted {num_transactions_deleted} transactions.", fg=typer.colors.GREEN)
        typer.secho(f"Successfully deleted {num_portfolios_deleted} portfolios.", fg=typer.colors.GREEN)
        typer.secho(f"Successfully deleted {num_assets_deleted} assets.", fg=typer.colors.GREEN)
    except Exception as e:
        db.rollback()
        typer.secho(f"An error occurred: {e}", fg=typer.colors.RED, err=True)


if __name__ == "__main__":
    app()