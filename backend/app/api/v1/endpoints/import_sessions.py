from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd
from typing import Any
import uuid

from app import crud
from app.core import dependencies as deps
from app.schemas.import_session import ImportSessionCreate, ImportSession
from app.models.user import User
from app.services.import_parsers.csv_parser import CsvParser
from app.services.import_parsers.zerodha_parser import ZerodhaParser
from app.services.import_parsers.icici_parser import IciciParser
from app.services.import_parsers.mf_cas_parser import MfCasParser

router = APIRouter()


def get_parser(file_name: str):
    if "zerodha" in file_name.lower():
        return ZerodhaParser()
    elif "icici" in file_name.lower():
        return IciciParser()
    elif "cas" in file_name.lower():
        return MfCasParser()
    else:
        return CsvParser() # Default to generic CSV parser

@router.post("/", response_model=ImportSession, status_code=status.HTTP_201_CREATED)
async def create_import_session(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create a new import session.
    """
    # Save the file temporarily
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Select and use the appropriate parser
    parser = get_parser(file.filename)
    try:
        parsed_data = parser.parse(file_location)
        if parsed_data.empty:
            raise HTTPException(status_code=400, detail="Failed to parse file.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    # Save the parsed data to a temporary file (e.g., Parquet)
    parsed_data_location = f"/tmp/{file.filename}.parquet"
    parsed_data.to_parquet(parsed_data_location)

    import_session_in = ImportSessionCreate(
        file_name=file.filename,
        file_path=file_location,
        parsed_file_path=parsed_data_location,
        status="PARSED",
    )

    import_session = crud.import_session.create_with_owner(
        db=db, obj_in=import_session_in, owner_id=current_user.id
    )
    return import_session


@router.get("/{session_id}/preview", response_model=list[dict[str, Any]])
def get_import_session_preview(
    session_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
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