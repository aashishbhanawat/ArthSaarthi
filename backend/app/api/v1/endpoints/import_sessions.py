import logging
import os
import shutil
import uuid
from pathlib import Path
from decimal import Decimal
from sqlalchemy.orm import Session
import pandas as pd
from typing import Any, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app import crud
from app import models, schemas
from app.core import dependencies as deps
from app.schemas.msg import Msg
from app.core.config import settings
from app.services.import_parsers.csv_parser import CsvParser
from app.services.import_parsers.zerodha_parser import ZerodhaParser
from app.services.import_parsers.icici_parser import IciciParser
from app.services.import_parsers.mf_cas_parser import MfCasParser

router = APIRouter()
log = logging.getLogger(__name__)


def get_parser(file_name: str):
    # if "zerodha" in file_name.lower():
    #     return ZerodhaParser()
    # elif "icici" in file_name.lower():
    #     return IciciParser()
    # elif "cas" in file_name.lower():
    #     return MfCasParser()
    # else:
    return CsvParser() # Default to generic CSV parser

@router.post("/", response_model=schemas.ImportSession, status_code=status.HTTP_201_CREATED)
async def create_import_session(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    portfolio_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
) -> Any:
    """
    Create new import session.
    This endpoint handles the file upload for a specific portfolio, saves it securely,
    parses it, and creates a session record in the database.
    """
    # 0. Verify user has access to the portfolio
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions for this portfolio")

    # 1. Securely save the uploaded file
    upload_dir = Path(settings.IMPORT_UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    
    # Sanitize filename and create a unique path to prevent overwrites and traversal attacks
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

    # 2. Create the initial ImportSession record with "UPLOADED" status
    parser = get_parser(file.filename)
    import_session_in = schemas.ImportSessionCreate(
        file_name=file.filename,
        file_path=str(temp_file_path),
        portfolio_id=portfolio_id,
        status="UPLOADED",
    )

    import_session = crud.import_session.create_with_owner(
        db=db, obj_in=import_session_in, owner_id=current_user.id
    )

    # 3. Select and use the appropriate parser
    try:
        parsed_data = parser.parse(str(temp_file_path))
        if parsed_data.empty:
            # Update status to FAILED if parsing is unsuccessful
            crud.import_session.update(db, db_obj=import_session, obj_in={"status": "FAILED"})
            raise HTTPException(status_code=400, detail="Failed to parse file. The file might be empty or in an unsupported format.")
    except Exception as e:
        log.error(f"Error parsing file {temp_file_path}: {e}")
        crud.import_session.update(db, db_obj=import_session, obj_in={"status": "FAILED"})
        raise HTTPException(status_code=400, detail=f"An error occurred during file parsing: {e}")

    # 4. Save the parsed data to a permanent, efficient format (e.g., Parquet)
    parsed_file_name = f"{import_session.id}.parquet"
    parsed_file_path = upload_dir / parsed_file_name
    parsed_data.to_parquet(parsed_file_path)

    # 5. Update the session with the parsed file path and "PARSED" status
    import_session_update = schemas.ImportSessionUpdate(
        parsed_file_path=str(parsed_file_path),
        status="PARSED"
    )
    import_session = crud.import_session.update(db, db_obj=import_session, obj_in=import_session_update)

    return import_session


@router.get("/{session_id}/preview", response_model=list[dict[str, Any]])
def get_import_session_preview(
    session_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    Get a preview of the parsed data for an import session.
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
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read parsed data: {e}")


@router.post("/{session_id}/commit", response_model=Msg)
def commit_import_session(
    session_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    Commit the transactions from an import session to the portfolio.
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
    if not import_session.parsed_file_path or not Path(import_session.parsed_file_path).exists():
        raise HTTPException(status_code=400, detail="No parsed file found for this session")

    try:
        df = pd.read_parquet(import_session.parsed_file_path)
                
        # Standardize column names to avoid issues with different file formats
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]

        # Define expected columns for a generic transaction import
        required_columns = {'ticker_symbol', 'transaction_type', 'quantity', 'price_per_unit', 'transaction_date'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"Parsed file is missing required columns: {', '.join(missing)}"
            )

        transactions_created = 0
        for _, row in df.iterrows():
            # 1. Find the asset by its ticker symbol
            asset = crud.asset.get_by_ticker(db, ticker_symbol=row['ticker_symbol'])
            if not asset:
                crud.import_session.update(db, db_obj=import_session, obj_in={"status": "FAILED", "error_message": f"Asset with ticker '{row['ticker_symbol']}' not found."})
                raise HTTPException(
                    status_code=400,
                    detail=f"Commit failed: Asset with ticker '{row['ticker_symbol']}' not found. Please create it first."
                )

            # 2. Prepare the transaction data from the row
            transaction_in = schemas.TransactionCreate(
                asset_id=asset.id,
                transaction_type=row['transaction_type'],
                quantity=Decimal(str(row['quantity'])),
                price_per_unit=Decimal(str(row['price_per_unit'])),
                transaction_date=pd.to_datetime(row['transaction_date']),
                fees=Decimal(str(row.get('fees', '0.0'))) # Handle optional fees column
            )

            # 3. Create the transaction using the existing CRUD method
            crud.transaction.create_with_portfolio(
                db=db, obj_in=transaction_in, portfolio_id=import_session.portfolio_id
            )
            transactions_created += 1

        # Update session status to COMPLETED
        crud.import_session.update(db, db_obj=import_session, obj_in={"status": "COMPLETED", "error_message": None})

        return {"msg": f"Successfully committed {transactions_created} transactions."}
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to be handled by FastAPI
        raise http_exc
    except Exception as e:
        log.error(f"Failed to commit import session {session_id}: {e}")
        crud.import_session.update(db, db_obj=import_session, obj_in={"status": "FAILED", "error_message": f"An unexpected error occurred during commit: {str(e)}"})
        raise HTTPException(status_code=500, detail=f"Could not commit transactions: {e}")