import logging
import os
import shutil
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, List, Optional

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
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.cache.utils import invalidate_caches_for_portfolio
from app.core import dependencies as deps
from app.core.config import settings
from app.schemas.msg import Msg
from app.services.import_parsers import parser_factory

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
    sanitized_filename = os.path.basename(file.filename)
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
        if file_extension == '.pdf':
            # PDF parsing - use password from form data if provided
            try:
                parsed_transactions = parser.parse(
                    str(temp_file_path), password=password
                )
            except ValueError as e:
                if "PASSWORD_REQUIRED" in str(e):
                    raise HTTPException(
                        status_code=422,
                        detail="PASSWORD_REQUIRED"
                    )
                raise
        elif file_extension in ['.xlsx', '.xls']:
            # Excel files - handle source-specific sheet/header requirements
            if source_type == "KFintech XLS":
                # KFintech XLS parser reads the file itself
                parsed_transactions = parser.parse(str(temp_file_path))
            elif source_type == "MFCentral CAS":
                df = pd.read_excel(
                    temp_file_path,
                    sheet_name='Transaction Details',
                    header=None  # MFCentral has header at row 8
                )
                parsed_transactions = parser.parse(df)
            elif source_type == "CAMS Statement":
                # CAMS has headers in row 0
                df = pd.read_excel(temp_file_path)
                parsed_transactions = parser.parse(df)
            else:
                # Generic Excel handling
                df = pd.read_excel(temp_file_path)
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
        log.error(f"Error parsing file {temp_file_path}: {e}")
        crud.import_session.update(
            db,
            db_obj=import_session,
            obj_in={"status": "FAILED", "error_message": str(e)},
        )
        raise HTTPException(
            status_code=400, detail=f"An error occurred during file parsing: {e}"
        )

    # 4. Save the list of Pydantic models to a Parquet file
    # Convert list of Pydantic models to a DataFrame for efficient storage
    parsed_df = pd.DataFrame([t.model_dump() for t in parsed_transactions])
    parsed_file_name = f"{import_session.id}.parquet"
    parsed_file_path = upload_dir / parsed_file_name
    parsed_df.to_parquet(parsed_file_path)

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
        df = pd.read_parquet(import_session.parsed_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read parsed data: {e}")

    valid_new: list[schemas.ParsedTransaction] = []
    duplicates: list[schemas.ParsedTransaction] = []
    invalid: list[dict] = []
    needs_mapping: list[schemas.ParsedTransaction] = []

    # Create a temporary map of pending aliases for quick lookup
    pending_alias_map = {
        alias.alias_symbol: alias.asset_id for alias in aliases_to_create
    }

    for _, row in df.iterrows():
        row_data = row.to_dict()
        parsed_transaction = schemas.ParsedTransaction(**row_data)

        # 1. Asset Identification
        ticker_symbol = row["ticker_symbol"]
        asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker_symbol)
        if asset:
            log.debug(f"Found asset by ticker: {ticker_symbol} -> {asset.name}")

        # If ticker looks like "ISIN:XXX", try to lookup by ISIN
        if not asset and ticker_symbol.startswith("ISIN:"):
            isin_code = ticker_symbol.replace("ISIN:", "")
            log.debug(f"Looking up by ISIN: {isin_code}")
            asset = db.query(models.Asset).filter(
                models.Asset.isin == isin_code
            ).first()
            if asset:
                log.info(f"Auto-matched by ISIN: {isin_code} -> {asset.name}")
            else:
                log.debug(f"No asset found with ISIN: {isin_code}")
                # Try to auto-create by looking up ISIN in AMFI
                # Check both isin (payout) and isin2 (reinvestment)
                from app.services.providers.amfi_provider import amfi_provider
                all_mf_data = amfi_provider.get_all_nav_data()
                for scheme_code, mf_info in all_mf_data.items():
                    isin_match = mf_info.get("isin") == isin_code
                    isin2_match = mf_info.get("isin2") == isin_code
                    if isin_match or isin2_match:
                        # Found in AMFI - create the asset
                        scheme = mf_info['scheme_name']
                        log.info(f"Found in AMFI: {isin_code} -> {scheme}")
                        asset = crud.asset.get_or_create_by_ticker(
                            db, ticker_symbol=scheme_code, asset_type="Mutual Fund"
                        )
                        if asset:
                            log.info(
                                f"Auto-created: {asset.name} ISIN {isin_code}"
                            )
                        break

        if not asset:
            # Check pending aliases from the current session first
            if ticker_symbol in pending_alias_map:
                asset_id = pending_alias_map[ticker_symbol]
                asset = crud.asset.get(db, id=asset_id)
                if asset:
                    log.debug(
                        f"Found in pending aliases: {ticker_symbol}"
                    )
            else:
                # Then check persisted aliases
                asset_alias = crud.asset_alias.get_by_alias(
                    db,
                    alias_symbol=ticker_symbol,
                    source=import_session.source,
                )
                if asset_alias:
                    asset = asset_alias.asset
                    log.debug(f"Found by alias: {ticker_symbol} -> {asset.name}")

        # NOTE: Fuzzy matching was removed because it caused incorrect mappings
        # (e.g., "Short Term" matching "Ultra Short Term").
        # For CAMS-style tickers, users must manually map via the mapping modal.

        if not asset:
            # If no asset or alias is found, it needs user mapping
            log.debug(f"No match found for: {ticker_symbol}")
            needs_mapping.append(parsed_transaction)
            continue

        # 2. Duplicate Detection
        existing_transaction = crud.transaction.get_by_details(
            db,
            portfolio_id=import_session.portfolio_id,
            asset_id=asset.id,
            transaction_date=pd.to_datetime(row["transaction_date"]),
            transaction_type=row["transaction_type"].upper(),
            quantity=Decimal(str(row["quantity"])),
            price_per_unit=Decimal(str(row["price_per_unit"])),
        )

        # For display: replace ISIN ticker with actual fund name/ticker
        if ticker_symbol.startswith("ISIN:") and asset:
            parsed_transaction.ticker_symbol = asset.name or asset.ticker_symbol

        if existing_transaction:
            duplicates.append(parsed_transaction)
        else:
            valid_new.append(parsed_transaction)

    log.info(f"Preview: {len(valid_new)} new, {len(duplicates)} duplicates, "
             f"{len(needs_mapping)} needs_mapping, {len(invalid)} invalid")

    return schemas.ImportSessionPreview(
        valid_new=valid_new,
        duplicates=duplicates,
        invalid=invalid,
        needs_mapping=needs_mapping,
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
            # Try to find asset by alias first, then by direct ticker, then by name
            asset = None
            ticker_symbol = parsed_tx.ticker_symbol

            # 1. Try alias lookup
            asset_alias = crud.asset_alias.get_by_alias(
                db,
                alias_symbol=ticker_symbol,
                source=import_session.source,
            )
            if asset_alias:
                asset = asset_alias.asset

            # 2. Try ticker lookup
            if not asset:
                asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker_symbol)

            # 3. Try ISIN lookup (if ticker is ISIN:XXX format)
            if not asset and ticker_symbol.startswith("ISIN:"):
                isin_code = ticker_symbol.replace("ISIN:", "")
                asset = db.query(models.Asset).filter(
                    models.Asset.isin == isin_code
                ).first()

            # 4. Try name lookup (for display-modified transactions)
            if not asset:
                asset = db.query(models.Asset).filter(
                    models.Asset.name == ticker_symbol
                ).first()

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
                fees=Decimal(str(parsed_tx.fees)),  # The ticker_symbol is intentionally
                # omitted here. The transaction is created using the asset_id resolved
                # from the alias, preventing a new lookup.
            )

            crud.transaction.create_with_portfolio(
                db=db, obj_in=transaction_in, portfolio_id=import_session.portfolio_id
            )
            transactions_created += 1

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

    except Exception as e:
        db.rollback()
        log.error(f"Failed to commit import session {session_id}: {e}")
        crud.import_session.update(
            db,
            db_obj=import_session,
            obj_in={
                "status": "FAILED",
                "error_message": (
                    f"An unexpected error occurred during commit: {str(e)}"
                ),
            },
        )
        db.commit()
        raise HTTPException(
            status_code=500, detail=f"Could not commit transactions: {e}"
        )
