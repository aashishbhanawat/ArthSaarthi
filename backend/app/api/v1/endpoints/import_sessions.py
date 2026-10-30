import logging
import shutil
import uuid
from datetime import date as date_type, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.cache.utils import invalidate_caches_for_portfolio
from app.core import dependencies as deps
from app.core.config import settings
from app.schemas.msg import Msg
from app.services.financial_data_service import financial_data_service
from app.services.import_parsers import parser_factory
from app.utils.filename import secure_filename
from app.utils.pydantic_compat import model_dump

router = APIRouter()
log = logging.getLogger(__name__)


@router.post(
    "/", response_model=schemas.ImportSession, status_code=status.HTTP_201_CREATED
)
async def create_import_session(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    portfolio_id: uuid.UUID = Form(...),
    source_type: str = Form(...),
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
) -> Any:
    """
    Create new import session.
    This endpoint handles the file upload, saves it, selects the correct parser
    based on the source_type, parses the data, and stores it for review.
    """
    # 0. Verify user has access to the portfolio
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not enough permissions for this portfolio"
        )

    # 1. Securely save the uploaded file
    upload_dir = Path(settings.IMPORT_UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    sanitized_filename = secure_filename(file.filename)
    temp_file_path = upload_dir / f"{uuid.uuid4()}_{sanitized_filename}"
    try:
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        log.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Could not save uploaded file.")
    finally:
        file.file.close()

    # 2. Create the initial ImportSession record
    import_session_in = schemas.ImportSessionCreate(
        file_name=file.filename,
        file_path=str(temp_file_path),
        portfolio_id=portfolio_id,
        source=source_type,
        status="UPLOADED",
    )
    import_session = crud.import_session.create_with_owner(
        db=db, obj_in=import_session_in, owner_id=current_user.id
    )

    # 3. Parse the file using the appropriate strategy
    try:
        # Load the uploaded file into a pandas DataFrame
        # Detect file type and use appropriate reader
        file_extension = temp_file_path.suffix.lower()

        # Get the correct parser from the factory
        parser = parser_factory.get_parser(source_type)

        # Handle PDF files differently - they use file path, not DataFrame
        if file_extension == ".pdf":
            # PDF parsing - use password from form data if provided
            try:
                parsed_transactions = parser.parse(
                    str(temp_file_path), password=password
                )
            except ValueError as e:
                if "PASSWORD_REQUIRED" in str(e):
                    raise HTTPException(status_code=422, detail="PASSWORD_REQUIRED")
                raise
        elif file_extension in [".xlsx", ".xls"]:
            # Excel files - handle source-specific sheet/header requirements
            if source_type == "KFintech XLS":
                # KFintech XLS parser reads the file itself
                parsed_transactions = parser.parse(str(temp_file_path))
            elif source_type == "MFCentral CAS":
                df = pd.read_excel(
                    temp_file_path,
                    sheet_name="Transaction Details",
                    header=None,  # MFCentral has header at row 8
                )
                parsed_transactions = parser.parse(df)
            elif source_type == "CAMS Statement":
                # CAMS has headers in row 0
                df = pd.read_excel(temp_file_path)
                parsed_transactions = parser.parse(df)
            elif source_type == "Zerodha Coin":
                # Zerodha Coin XLSX has branding/info rows at top
                # Actual header is at row 14
                df = pd.read_excel(temp_file_path, skiprows=14)
                # Normalize column names to lowercase for consistency
                df.columns = df.columns.str.lower().str.replace(" ", "_")
                parsed_transactions = parser.parse(df)
            elif source_type == "Zerodha Dividend":
                # Zerodha Dividend XLSX has branding/info rows at top
                # Actual header is at row 14
                df = pd.read_excel(temp_file_path, skiprows=14)
                # Normalize column names to lowercase for consistency
                df.columns = df.columns.str.lower().str.replace(" ", "_")
                parsed_transactions = parser.parse(df)
            elif source_type == "ICICI Direct Portfolio Equity":
                # ICICI exports TSV data with a fake .xls extension.
                # Try real Excel first, fall back to TSV.
                try:
                    engine = "xlrd" if file_extension == ".xls" else None
                    df = pd.read_excel(temp_file_path, engine=engine)
                except Exception:
                    # File is likely TSV/CSV with .xls extension
                    df = pd.read_csv(temp_file_path, sep="\t")
                parsed_transactions = parser.parse(df)
            else:
                # Generic Excel handling — also handles fake .xls
                try:
                    engine = "xlrd" if file_extension == ".xls" else None
                    df = pd.read_excel(temp_file_path, engine=engine)
                except Exception:
                    df = pd.read_csv(temp_file_path, sep="\t")
                # Parse the dataframe into a list of Pydantic models
                parsed_transactions = parser.parse(df)
        else:
            # CSV files
            df = pd.read_csv(temp_file_path)
            # Parse the dataframe into a list of Pydantic models
            parsed_transactions = parser.parse(df)

        # Sort transactions: by date, then ticker, then type (BUY before SELL)
        parsed_transactions.sort(
            key=lambda x: (
                x.transaction_date,
                x.ticker_symbol,
                0 if x.transaction_type.upper() == "BUY" else 1,
            )
        )

        if not parsed_transactions:
            crud.import_session.update(
                db,
                db_obj=import_session,
                obj_in={
                    "status": "FAILED",
                    "error_message": "No transactions found in file.",
                },
            )
            raise HTTPException(
                status_code=400,
                detail="Failed to parse file. No valid transactions were found.",
            )
    except HTTPException:
        # Re-raise HTTP exceptions (like PASSWORD_REQUIRED) without wrapping
        raise
    except Exception as e:
        log.error(f"Error parsing file {temp_file_path}: {e}", exc_info=True)
        crud.import_session.update(
            db,
            db_obj=import_session,
            obj_in={
                "status": "FAILED",
                "error_message": "An error occurred during file parsing.",
            },
        )
        raise HTTPException(
            status_code=400, detail="An error occurred during file parsing."
        )

    # 4. Save the list of Pydantic models to a JSON file (Android compatible)
    # Convert list of Pydantic models to a DataFrame for efficient storage
    parsed_df = pd.DataFrame([model_dump(t) for t in parsed_transactions])
    parsed_file_name = f"{import_session.id}.json"
    parsed_file_path = upload_dir / parsed_file_name
    parsed_df.to_json(parsed_file_path, orient="records", date_format="iso")

    # 5. Update the session with the parsed file path and "PARSED" status
    import_session_update = schemas.ImportSessionUpdate(
        parsed_file_path=str(parsed_file_path), status="PARSED"
    )
    import_session = crud.import_session.update(
        db, db_obj=import_session, obj_in=import_session_update
    )

    db.commit()
    db.refresh(import_session)

    return import_session


@router.get("/{session_id}", response_model=schemas.ImportSession)
def get_import_session(
    session_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    Get an import session by ID.
    """
    import_session = crud.import_session.get(db=db, id=session_id)
    if not import_session:
        raise HTTPException(status_code=404, detail="Import session not found")
    if import_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return import_session


def resolve_asset_for_import_transaction(
    db: Session,
    ticker_symbol: Optional[str],
    source: Optional[str] = None,
    name: Optional[str] = None,
    isin: Optional[str] = None,
    pending_alias_map: Optional[Dict[str, uuid.UUID]] = None,
) -> Optional[models.Asset]:
    """Resolves an import transaction to a system Asset using:
    1. ISIN code
    2. Pending aliases from current preview mapping
    3. Direct ticker symbol (full ticker or base without exchange suffix)
    4. Exact/compatible broker aliases (e.g. ICICI Tradebook aliases like BOMBUR -> BBTC)
    5. Global aliases across any source
    6. Exact name matching
    """
    if not ticker_symbol and not isin and not name:
        return None

    # 1. Try ISIN lookup first
    if isin:
        asset = crud.asset.get_by_isin(db, isin_code=isin)
        if asset:
            return asset

    # Build symbol candidate variations (e.g. ['BOMBUR.NS', 'BOMBUR'])
    candidates: List[str] = []
    if ticker_symbol:
        candidates.append(ticker_symbol)
        base = ticker_symbol.rsplit(".", 1)[0] if "." in ticker_symbol else ticker_symbol
        if base and base not in candidates:
            candidates.append(base)
    if name and name not in candidates:
        candidates.append(name)

    # 2. Check pending aliases (from current preview session)
    if pending_alias_map:
        for c in candidates:
            if c in pending_alias_map:
                asset = crud.asset.get(db, id=pending_alias_map[c])
                if asset:
                    return asset

    # 3. Direct asset ticker lookup (full symbol, base symbol, base with .NS/.BO)
    for c in candidates:
        if c.upper().startswith("ISIN:"):
            continue
        asset = crud.asset.get_by_ticker(db, ticker_symbol=c)
        if asset:
            return asset
        if "." not in c:
            for suffix in (".NS", ".BO"):
                asset = crud.asset.get_by_ticker(db, ticker_symbol=f"{c}{suffix}")
                if asset:
                    return asset

    # 4. Alias lookup with source or compatible broker sources
    sources_to_try: List[str] = []
    if source:
        sources_to_try.append(source)
        src_lower = source.lower()
        if "icici" in src_lower or "breeze" in src_lower:
            for s in ("ICICI Direct Tradebook", "ICICI Direct", "icici_breeze_api", "ICICI Breeze"):
                if s not in sources_to_try:
                    sources_to_try.append(s)
        elif "zerodha" in src_lower or "kite" in src_lower:
            for s in ("Zerodha Tradebook", "Zerodha", "zerodha_kite_api"):
                if s not in sources_to_try:
                    sources_to_try.append(s)

    for c in candidates:
        for s in sources_to_try:
            asset_alias = crud.asset_alias.get_by_alias(db, alias_symbol=c, source=s)
            if asset_alias and asset_alias.asset:
                return asset_alias.asset

    # 5. Alias lookup across ANY source
    for c in candidates:
        asset_alias = (
            db.query(models.AssetAlias)
            .filter(models.AssetAlias.alias_symbol == c)
            .first()
        )
        if asset_alias and asset_alias.asset:
            return asset_alias.asset

    # 6. Asset name lookup
    for c in candidates:
        asset = db.query(models.Asset).filter(models.Asset.name == c).first()
        if asset:
            return asset

    return None


@router.post("/{session_id}/preview", response_model=schemas.ImportSessionPreview)
def get_import_session_preview(
    session_id: uuid.UUID,
    aliases_to_create: List[schemas.AssetAliasCreate] = Body(default=[]),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a categorized preview of the parsed data for an import session,
    identifying new, duplicate, and invalid transactions.
    """
    import_session = crud.import_session.get(db=db, id=session_id)
    if not import_session:
        raise HTTPException(status_code=404, detail="Import session not found")
    if import_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not import_session.parsed_file_path:
        raise HTTPException(status_code=400, detail="No parsed file for this session")

    try:
        df = pd.read_json(import_session.parsed_file_path, orient="records")
        # Replace NaN/NaT with None for Pydantic compatibility
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        log.error(f"Could not read parsed data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not read parsed data.")

    valid_new: list[schemas.ParsedTransaction] = []
    duplicates: list[schemas.ParsedTransaction] = []
    invalid: list[dict] = []
    needs_mapping: list[schemas.ParsedTransaction] = []

    # Create a temporary map of pending aliases for quick lookup
    pending_alias_map = {
        alias.alias_symbol: alias.asset_id for alias in aliases_to_create
    }

    try:
        for _, row in df.iterrows():
            # Clean NaNs to None to avoid validation errors for optional fields
            row_data = {k: (None if pd.isna(v) else v) for k, v in row.items()}
            try:
                parsed_transaction = schemas.ParsedTransaction(**row_data)
            except Exception as e:
                log.error(f"Validation error for row: {row_data}. Error: {e}")
                invalid.append({"row_data": row_data, "error": str(e)})
                continue

            # 1. Asset Identification
            ticker_symbol = row_data.get("ticker_symbol") or ""
            isin_code = row_data.get("isin")
            name_val = row_data.get("name")
            asset = resolve_asset_for_import_transaction(
                db=db,
                ticker_symbol=ticker_symbol,
                source=import_session.source,
                name=name_val,
                isin=isin_code,
                pending_alias_map=pending_alias_map,
            )

            # If ISIN lookup externally for new mutual funds (side-effect free preview)
            if not asset and isin_code:
                details = financial_data_service.get_asset_details(
                    f"ISIN:{isin_code}"
                )
                if details:
                    # Validate and filter through schema to prevent TypeError
                    asset_in = schemas.AssetCreate(
                        ticker_symbol=(
                            details.get("ticker_symbol")
                            or f"ISIN:{isin_code}".upper()
                        ),
                        **{
                            k: v for k, v in details.items() if k != "ticker_symbol"
                        },
                    )
                    asset = models.Asset(**model_dump(asset_in))
                if asset:
                    log.debug(f"Found asset by ISIN: {isin_code} -> {asset.name}")

            # If ticker looks like "ISIN:XXX", try to find externally
            # (side-effect free preview)
            if not asset and ticker_symbol.upper().startswith("ISIN:"):
                details = financial_data_service.get_asset_details(ticker_symbol)
                if details:
                    # Validate and filter through schema to prevent TypeError
                    asset_in = schemas.AssetCreate(
                        ticker_symbol=(
                            details.get("ticker_symbol") or ticker_symbol.upper()
                        ),
                        **{k: v for k, v in details.items() if k != "ticker_symbol"},
                    )
                    asset = models.Asset(**model_dump(asset_in))
                if asset:
                    log.info(
                        f"Auto-matched (transient) by ISIN: {ticker_symbol} "
                        f"-> {asset.name}"
                    )

            if not asset:
                # If no asset or alias is found, it needs user mapping
                log.debug(f"No match found for: {ticker_symbol}")
                if parsed_transaction.ticker_symbol and parsed_transaction.ticker_symbol.endswith((".NS", ".BO")):
                    parsed_transaction.ticker_symbol = parsed_transaction.ticker_symbol.rsplit(".", 1)[0]
                needs_mapping.append(parsed_transaction)
                continue

            # Update display ticker symbol to canonical resolved ticker if it was mapped via alias
            if asset and asset.ticker_symbol:
                parsed_transaction.ticker_symbol = asset.ticker_symbol
            elif parsed_transaction.ticker_symbol and parsed_transaction.ticker_symbol.endswith((".NS", ".BO")):
                parsed_transaction.ticker_symbol = parsed_transaction.ticker_symbol.rsplit(".", 1)[0]

            # 2. Duplicate Detection
            existing_transaction = None
            # Only check duplicates if the asset already exists in the database
            # We use inspect(asset).persistent to check if it's attached
            if asset and getattr(asset, "id", None) and inspect(asset).persistent:
                existing_transaction = crud.transaction.get_by_details(
                    db,
                    portfolio_id=import_session.portfolio_id,
                    asset_id=asset.id,
                    transaction_date=pd.to_datetime(row_data["transaction_date"]),
                    transaction_type=row_data["transaction_type"].upper(),
                    quantity=Decimal(str(row_data["quantity"])),
                    price_per_unit=Decimal(str(row_data["price_per_unit"])),
                )

            # For display: replace ISIN ticker with actual fund name/ticker
            if ticker_symbol.startswith("ISIN:") and asset:
                parsed_transaction.ticker_symbol = asset.name or asset.ticker_symbol

            if existing_transaction:
                duplicates.append(parsed_transaction)
            else:
                valid_new.append(parsed_transaction)

        log.info(
            f"Preview: {len(valid_new)} new, {len(duplicates)} duplicates, "
            f"{len(needs_mapping)} needs_mapping, {len(invalid)} invalid"
        )

        return schemas.ImportSessionPreview(
            valid_new=valid_new,
            duplicates=duplicates,
            invalid=invalid,
            needs_mapping=needs_mapping,
        )
    except Exception as e:
        log.error(f"Error in get_import_session_preview: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Could not retrieve import session preview."
        )


@router.post("/{session_id}/commit", response_model=Msg)
def commit_import_session(
    session_id: uuid.UUID,
    commit_payload: schemas.ImportSessionCommit,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    Commit the selected transactions from an import session to the portfolio.
    This also handles the creation of new asset aliases.
    """
    import_session = crud.import_session.get(db=db, id=session_id)
    if not import_session:
        raise HTTPException(status_code=404, detail="Import session not found")
    if import_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if import_session.status != "PARSED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot commit session with status '{import_session.status}'",
        )

    try:
        # 1. Create any new asset aliases that the user has defined.
        for alias_in in commit_payload.aliases_to_create:
            crud.asset_alias.create(db, obj_in=alias_in)

        # 2. Commit the selected transactions.
        transactions_created = 0
        for parsed_tx in commit_payload.transactions_to_commit:
            # Try to find asset: ISIN first, then robust symbol/alias resolution
            ticker_symbol = parsed_tx.ticker_symbol
            asset = resolve_asset_for_import_transaction(
                db=db,
                ticker_symbol=ticker_symbol,
                source=import_session.source,
                name=getattr(parsed_tx, "name", None),
                isin=parsed_tx.isin,
            )

            # Fallback for transient ISIN creation if not exists
            if not asset and parsed_tx.isin:
                asset = crud.asset.get_or_create_by_ticker(
                    db, ticker_symbol=f"ISIN:{parsed_tx.isin}"
                )
            if not asset and ticker_symbol and ticker_symbol.upper().startswith("ISIN:"):
                asset = crud.asset.get_or_create_by_ticker(
                    db, ticker_symbol=ticker_symbol
                )

            if not asset:
                log.error(
                    f"Asset '{parsed_tx.ticker_symbol}' not found during commit for "
                    f"session {session_id}"
                )
                continue

            transaction_in = schemas.TransactionCreate(
                asset_id=asset.id,
                transaction_type=parsed_tx.transaction_type.upper(),
                quantity=Decimal(str(parsed_tx.quantity)),
                price_per_unit=Decimal(str(parsed_tx.price_per_unit)),
                transaction_date=pd.to_datetime(parsed_tx.transaction_date),
                fees=Decimal(str(parsed_tx.fees)),
            )

            try:
                crud.transaction.create_with_portfolio(
                    db=db,
                    obj_in=transaction_in,
                    portfolio_id=import_session.portfolio_id,
                )
                transactions_created += 1
            except HTTPException as he:
                db.rollback()
                error_detail = he.detail
                # Enhance error message with ticker if it's a holdings error
                if "Insufficient holdings" in str(error_detail):
                    error_detail = f"{asset.ticker_symbol}: {error_detail}"

                log.error(
                    f"Failed to commit transaction for {asset.ticker_symbol} "
                    f"in session {session_id}: {error_detail}"
                )

                # Update session status to FAILED and store the detailed error
                crud.import_session.update(
                    db,
                    db_obj=import_session,
                    obj_in={
                        "status": "FAILED",
                        "error_message": error_detail,
                    },
                )
                db.commit()
                # Re-raise with the detailed message
                raise HTTPException(status_code=he.status_code, detail=error_detail)

        # 3. Update session status to COMPLETED
        crud.import_session.update(
            db,
            db_obj=import_session,
            obj_in={"status": "COMPLETED", "error_message": None},
        )

        db.commit()

        # Invalidate cache after successful commit
        invalidate_caches_for_portfolio(db, portfolio_id=import_session.portfolio_id)

        return {"msg": f"Successfully committed {transactions_created} transactions."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        log.error(
            f"Failed to commit import session {session_id}: {error_msg}", exc_info=True
        )
        crud.import_session.update(
            db,
            db_obj=import_session,
            obj_in={
                "status": "FAILED",
                "error_message": f"Unexpected error: {error_msg}",
            },
        )
        db.commit()
        raise HTTPException(status_code=500, detail="Could not commit transactions.")


@router.post(
    "/fd", response_model=schemas.ImportSession, status_code=status.HTTP_201_CREATED
)
async def create_fd_import_session(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    portfolio_id: uuid.UUID = Form(...),
    source_type: str = Form(...),
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
) -> Any:
    """
    Create new FD import session from bank statement.
    """
    # 0. Verify user has access to the portfolio
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not enough permissions for this portfolio"
        )

    # 1. Securely save the uploaded file
    upload_dir = Path(settings.IMPORT_UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    sanitized_filename = secure_filename(file.filename)
    temp_file_path = upload_dir / f"{uuid.uuid4()}_{sanitized_filename}"
    try:
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        log.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Could not save uploaded file.")
    finally:
        file.file.close()

    # 2. Create the initial ImportSession record
    import_session_in = schemas.ImportSessionCreate(
        file_name=file.filename,
        file_path=str(temp_file_path),
        portfolio_id=portfolio_id,
        source=source_type,
        status="UPLOADED",
    )
    import_session = crud.import_session.create_with_owner(
        db=db, obj_in=import_session_in, owner_id=current_user.id
    )

    # 3. Parse the FD statement
    try:
        parser = parser_factory.get_parser(source_type)
        try:
            parsed_fds = parser.parse(str(temp_file_path), password=password)
        except ValueError as e:
            if "PASSWORD_REQUIRED" in str(e):
                raise HTTPException(status_code=422, detail="PASSWORD_REQUIRED")
            raise

        if not parsed_fds:
            crud.import_session.update(
                db,
                db_obj=import_session,
                obj_in={
                    "status": "FAILED",
                    "error_message": "No FD data found in file.",
                },
            )
            raise HTTPException(
                status_code=400,
                detail="Failed to parse file. No valid FD details were found.",
            )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error parsing FD file {temp_file_path}: {e}", exc_info=True)
        crud.import_session.update(
            db,
            db_obj=import_session,
            obj_in={
                "status": "FAILED",
                "error_message": "An error occurred during file parsing.",
            },
        )
        raise HTTPException(
            status_code=400, detail="An error occurred during file parsing."
        )

    # 4. Save the list of Pydantic models to a JSON file
    parsed_df = pd.DataFrame([model_dump(t) for t in parsed_fds])
    parsed_file_name = f"fd_{import_session.id}.json"
    parsed_file_path = upload_dir / parsed_file_name
    parsed_df.to_json(parsed_file_path, orient="records", date_format="iso")

    # 5. Update the session
    import_session_update = schemas.ImportSessionUpdate(
        parsed_file_path=str(parsed_file_path), status="PARSED"
    )
    import_session = crud.import_session.update(
        db, db_obj=import_session, obj_in=import_session_update
    )

    db.commit()
    db.refresh(import_session)

    return import_session


@router.post("/{session_id}/fd-preview", response_model=schemas.FDImportPreview)
def get_fd_import_session_preview(
    session_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get preview of parsed FDs, flagging duplicates by account_number and start_date.
    """
    import_session = crud.import_session.get(db=db, id=session_id)
    if not import_session:
        raise HTTPException(status_code=404, detail="Import session not found")
    if import_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not import_session.parsed_file_path:
        raise HTTPException(status_code=400, detail="No parsed file for this session")

    try:
        df = pd.read_json(import_session.parsed_file_path, orient="records")
        # Replace NaN/NaT with None for Pydantic compatibility
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        log.error(f"Could not read parsed data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not read parsed data.")

    parsed_fds: List[schemas.ParsedFixedDeposit] = []
    duplicates: List[schemas.ParsedFixedDeposit] = []

    # Get existing FDs for the portfolio for duplicate detection
    existing_fds = (
        db.query(models.FixedDeposit)
        .filter(models.FixedDeposit.portfolio_id == import_session.portfolio_id)
        .all()
    )

    # Create an lookup set for (account_number, start_date)
    existing_lookup = {
        (fd.account_number, fd.start_date.strftime("%Y-%m-%d"))
        for fd in existing_fds
        if fd.account_number and fd.start_date
    }

    try:
        for _, row in df.iterrows():
            # Clean NaNs to None to avoid validation errors for optional fields
            fd_data = {k: (None if pd.isna(v) else v) for k, v in row.items()}
            try:
                parsed_fd = schemas.ParsedFixedDeposit(**fd_data)
            except Exception as e:
                log.error(f"Validation error for row: {fd_data}. Error: {e}")
                continue

            # Duplicate detection: match both account number AND start date
            # Renewals (same account_number, diff start_date) are NOT duplicates.
            if (parsed_fd.account_number, parsed_fd.start_date) in existing_lookup:
                duplicates.append(parsed_fd)
            else:
                parsed_fds.append(parsed_fd)

        return schemas.FDImportPreview(
            parsed_fds=parsed_fds,
            duplicates=duplicates,
        )
    except Exception as e:
        log.error(f"Error in get_fd_import_session_preview: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Could not retrieve FD import session preview."
        )


@router.post("/{session_id}/fd-commit", response_model=Msg)
def commit_fd_import_session(
    session_id: uuid.UUID,
    commit_payload: schemas.FDImportCommit,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Commit selected FDs to the portfolio.
    """
    import_session = crud.import_session.get(db=db, id=session_id)
    if not import_session:
        raise HTTPException(status_code=404, detail="Import session not found")
    if import_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if import_session.status != "PARSED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot commit session with status '{import_session.status}'",
        )

    try:
        fds_created = 0
        for parsed_fd in commit_payload.fds_to_commit:
            fd_in = schemas.FixedDepositCreate(
                name=f"{parsed_fd.bank} FD - {parsed_fd.account_number}",
                account_number=parsed_fd.account_number,
                principal_amount=Decimal(str(parsed_fd.principal_amount)),
                interest_rate=Decimal(str(parsed_fd.interest_rate)),
                start_date=date_type.fromisoformat(
                    str(parsed_fd.start_date).split("T")[0]
                ),
                maturity_date=date_type.fromisoformat(
                    str(parsed_fd.maturity_date).split("T")[0]
                ),
                compounding_frequency=parsed_fd.compounding_frequency,
                interest_payout=parsed_fd.interest_payout,
                portfolio_id=import_session.portfolio_id,
            )

            crud.fixed_deposit.create_with_portfolio(
                db=db, obj_in=fd_in, user_id=current_user.id
            )
            fds_created += 1

        # Update session status
        crud.import_session.update(
            db,
            db_obj=import_session,
            obj_in={"status": "COMPLETED", "error_message": None},
        )

        db.commit()
        invalidate_caches_for_portfolio(db, portfolio_id=import_session.portfolio_id)

        return {"msg": f"Successfully imported {fds_created} Fixed Deposits."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        log.error(
            f"Failed to commit FD import session {session_id}: {error_msg}",
            exc_info=True,
        )
        crud.import_session.update(
            db,
            db_obj=import_session,
            obj_in={
                "status": "FAILED",
                "error_message": f"Unexpected error: {error_msg}",
            },
        )
        db.commit()
        raise HTTPException(status_code=500, detail="Could not commit FDs.")


@router.post(
    "/broker/sync",
    response_model=schemas.ImportSession,
    status_code=status.HTTP_201_CREATED,
)
async def create_broker_sync_import_session(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    sync_req: schemas.BrokerSyncRequest = Body(...),
) -> Any:
    """
    Create a new import session directly from a connected broker API (Zerodha Kite / ICICI Breeze).
    Pulls holdings or trade history directly, standardizes records, and stages an ImportSession.
    """
    try:
        log.info(
            f"Initiating broker sync for provider '{sync_req.provider_name}', "
            f"portfolio '{sync_req.portfolio_id}', type '{sync_req.import_type}'"
        )
        portfolio = crud.portfolio.get(db=db, id=sync_req.portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if portfolio.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions for this portfolio"
            )

        provider_name = sync_req.provider_name.lower()
        cred = crud.crud_broker.get_by_user_and_provider(
            db, user_id=current_user.id, provider_name=provider_name
        )
        if not cred or not cred.is_active or not cred.encrypted_access_token:
            log.warning(f"No active session found for broker '{provider_name}'.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"No active session for broker '{provider_name}'. Please authenticate via Broker Settings.",
            )

        if cred.token_expires_at and cred.token_expires_at < datetime.now(timezone.utc):
            log.warning(f"Broker session token for '{provider_name}' has expired.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Broker session token for '{provider_name}' has expired. Please re-authenticate.",
            )

        token = crud.crud_broker.get_decrypted_token(cred)
        secret = crud.crud_broker.get_decrypted_secret(cred)

        if not token:
            log.warning(f"Decrypted token for '{provider_name}' is empty.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Broker session token for '{provider_name}' is unauthenticated. Please re-authenticate.",
            )

        if provider_name == "zerodha_kite":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Direct API import is disabled for Zerodha Kite because Kite Connect API "
                    "does not provide historical trade logs or purchase dates. Please import your transactions "
                    "by downloading your Tradebook CSV from Zerodha Console (Reports > Tradebook) and uploading "
                    "it using the File Upload tab."
                ),
            )

        elif provider_name == "icici_breeze":
            from app.services.providers.icici_breeze_provider import IciciBreezeProvider

            provider = IciciBreezeProvider(
                api_key=cred.api_key, session_token=token, api_secret=secret
            )
            try:
                if sync_req.import_type == "trades":
                    from_date_obj = (
                        date_type.fromisoformat(sync_req.from_date)
                        if sync_req.from_date
                        else None
                    )
                    to_date_obj = (
                        date_type.fromisoformat(sync_req.to_date)
                        if sync_req.to_date
                        else None
                    )
                    raw_data = provider.fetch_trades(
                        from_date=from_date_obj, to_date=to_date_obj
                    )
                else:
                    raw_data = provider.fetch_holdings()
            except PermissionError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="ICICI Breeze session token is invalid or expired. Please re-authenticate via Broker Settings.",
                )
            except (httpx.RequestError, OSError, ConnectionError) as net_err:
                log.error(f"ICICI Breeze API network error: {net_err}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Unable to reach ICICI Breeze server. Network error: {net_err}",
                )
            from app.services.import_parsers.broker_api_parser import parse_icici_api_payload

            parsed_items = parse_icici_api_payload(
                raw_data,
                import_type=sync_req.import_type,
                default_portfolio_id=str(sync_req.portfolio_id),
                as_of_date=sync_req.as_of_date or sync_req.from_date,
            )

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported broker provider '{provider_name}'"
            )

        if not parsed_items:
            log.warning(
                f"No {sync_req.import_type} records returned by broker provider '{provider_name}'."
            )
            if provider_name == "zerodha_kite" and sync_req.import_type == "trades":
                detail_msg = (
                    "No trades were executed today in your Zerodha Kite account. "
                    "Note: Zerodha Kite Connect API only returns trades executed on the current trading day. "
                    "Zerodha does not provide an API for historical trade logs. To import past trades, please "
                    "download your Tradebook CSV from Zerodha Console (Reports > Tradebook) and import it using the File Upload tab."
                )
            else:
                detail_msg = f"No {sync_req.import_type} records found for your {provider_name.replace('_', ' ').title()} account for the specified date range."

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_msg,
            )

        session_id = uuid.uuid4()
        upload_dir = Path(settings.IMPORT_UPLOAD_DIR)
        upload_dir.mkdir(exist_ok=True)
        parsed_file_path = upload_dir / f"parsed_{session_id}.json"

        df = pd.DataFrame(parsed_items)
        df.to_json(parsed_file_path, orient="records", date_format="iso")

        import_session_in = schemas.ImportSessionCreate(
            file_name=f"{provider_name}_{sync_req.import_type}_sync.json",
            file_path=str(parsed_file_path),
            portfolio_id=sync_req.portfolio_id,
            source=f"{provider_name}_api",
            status="PARSED",
        )

        import_session = crud.import_session.create_with_owner(
            db=db, obj_in=import_session_in, owner_id=current_user.id
        )

        crud.import_session.update(
            db=db,
            db_obj=import_session,
            obj_in=schemas.ImportSessionUpdate(
                parsed_file_path=str(parsed_file_path), status="PARSED"
            ),
        )

        db.commit()
        db.refresh(import_session)
        log.info(f"Successfully created broker sync import session {import_session.id} with {len(parsed_items)} records.")
        return import_session

    except HTTPException:
        raise
    except PermissionError as pe:
        log.warning(f"Broker permission error during sync: {pe}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Broker authentication failed or expired: {str(pe)}",
        )
    except Exception as e:
        db.rollback()
        log.error(f"Failed to create broker sync import session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync from broker API: {str(e)}",
        )


