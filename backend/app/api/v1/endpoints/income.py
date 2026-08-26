import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import dependencies
from app.crud.crud_income import crud_income_entry, crud_income_source

router = APIRouter()


# ---------------------------------------------------------------------------
# Income Sources
# ---------------------------------------------------------------------------

@router.get("/sources", response_model=List[schemas.IncomeSource])
def read_income_sources(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve income sources for the current user.
    """
    return crud_income_source.get_multi_by_owner(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.post("/sources", response_model=schemas.IncomeSource, status_code=201)
def create_income_source(
    *,
    db: Session = Depends(dependencies.get_db),
    source_in: schemas.IncomeSourceCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create a new income source.
    """
    return crud_income_source.create_with_owner(
        db=db, obj_in=source_in, user_id=current_user.id
    )


@router.put("/sources/{source_id}", response_model=schemas.IncomeSource)
def update_income_source(
    *,
    db: Session = Depends(dependencies.get_db),
    source_id: uuid.UUID,
    source_in: schemas.IncomeSourceUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update an existing income source.
    """
    source = crud_income_source.get_by_id_and_owner(
        db=db, id=source_id, user_id=current_user.id
    )
    if not source:
        raise HTTPException(status_code=404, detail="Income source not found")

    updated = crud_income_source.update(db=db, db_obj=source, obj_in=source_in)
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/sources/{source_id}", response_model=schemas.IncomeSource)
def delete_income_source(
    *,
    db: Session = Depends(dependencies.get_db),
    source_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete an income source.
    """
    source = crud_income_source.get_by_id_and_owner(
        db=db, id=source_id, user_id=current_user.id
    )
    if not source:
        raise HTTPException(status_code=404, detail="Income source not found")

    deleted = crud_income_source.remove(db=db, id=source_id)
    db.commit()
    return deleted


# ---------------------------------------------------------------------------
# Income Entries
# ---------------------------------------------------------------------------

@router.get("/entries", response_model=List[schemas.IncomeEntry])
def read_income_entries(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
    financial_year: Optional[str] = Query(None, description="e.g. 2025-2026"),
    source_id: Optional[uuid.UUID] = Query(None),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve income entries for the current user.
    """
    entries = crud_income_entry.get_multi_by_owner(
        db=db,
        user_id=current_user.id,
        financial_year=financial_year,
        source_id=source_id,
        skip=skip,
        limit=limit,
    )
    result = []
    for entry in entries:
        e_dict = {
            "id": entry.id,
            "user_id": entry.user_id,
            "source_id": entry.source_id,
            "financial_year": entry.financial_year,
            "entry_date": entry.entry_date,
            "gross_amount": entry.gross_amount,
            "tds_amount": entry.tds_amount,
            "net_amount": entry.net_amount,
            "notes": entry.notes,
            "source_name": entry.source.name if entry.source else None,
            "source_category": entry.source.category if entry.source else None,
        }
        result.append(e_dict)
    return result


@router.post("/entries", response_model=schemas.IncomeEntry, status_code=201)
def create_income_entry(
    *,
    db: Session = Depends(dependencies.get_db),
    entry_in: schemas.IncomeEntryCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create a new income entry.
    """
    # Verify source belongs to current user
    source = crud_income_source.get_by_id_and_owner(
        db=db, id=entry_in.source_id, user_id=current_user.id
    )
    if not source:
        raise HTTPException(
            status_code=400, detail="Invalid source_id or source does not belong to user"
        )

    entry = crud_income_entry.create_with_owner(
        db=db, obj_in=entry_in, user_id=current_user.id
    )
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "source_id": entry.source_id,
        "financial_year": entry.financial_year,
        "entry_date": entry.entry_date,
        "gross_amount": entry.gross_amount,
        "tds_amount": entry.tds_amount,
        "net_amount": entry.net_amount,
        "notes": entry.notes,
        "source_name": source.name,
        "source_category": source.category,
    }


@router.put("/entries/{entry_id}", response_model=schemas.IncomeEntry)
def update_income_entry(
    *,
    db: Session = Depends(dependencies.get_db),
    entry_id: uuid.UUID,
    entry_in: schemas.IncomeEntryUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update an existing income entry.
    """
    entry = crud_income_entry.get_by_id_and_owner(
        db=db, id=entry_id, user_id=current_user.id
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Income entry not found")

    if entry_in.source_id is not None:
        source = crud_income_source.get_by_id_and_owner(
            db=db, id=entry_in.source_id, user_id=current_user.id
        )
        if not source:
            raise HTTPException(
                status_code=400, detail="Invalid source_id or source does not belong to user"
            )

    try:
        updated_entry = crud_income_entry.update_with_owner(
            db=db, db_obj=entry, obj_in=entry_in
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": updated_entry.id,
        "user_id": updated_entry.user_id,
        "source_id": updated_entry.source_id,
        "financial_year": updated_entry.financial_year,
        "entry_date": updated_entry.entry_date,
        "gross_amount": updated_entry.gross_amount,
        "tds_amount": updated_entry.tds_amount,
        "net_amount": updated_entry.net_amount,
        "notes": updated_entry.notes,
        "source_name": updated_entry.source.name if updated_entry.source else None,
        "source_category": updated_entry.source.category if updated_entry.source else None,
    }


@router.delete("/entries/{entry_id}", response_model=schemas.IncomeEntry)
def delete_income_entry(
    *,
    db: Session = Depends(dependencies.get_db),
    entry_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete an income entry.
    """
    entry = crud_income_entry.get_by_id_and_owner(
        db=db, id=entry_id, user_id=current_user.id
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Income entry not found")

    source_name = entry.source.name if entry.source else None
    source_cat = entry.source.category if entry.source else None
    deleted = crud_income_entry.remove(db=db, id=entry_id)
    db.commit()

    return {
        "id": deleted.id,
        "user_id": deleted.user_id,
        "source_id": deleted.source_id,
        "financial_year": deleted.financial_year,
        "entry_date": deleted.entry_date,
        "gross_amount": deleted.gross_amount,
        "tds_amount": deleted.tds_amount,
        "net_amount": deleted.net_amount,
        "notes": deleted.notes,
        "source_name": source_name,
        "source_category": source_cat,
    }


@router.get("/summary", response_model=schemas.IncomeFYSummary)
def get_income_summary(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
    financial_year: str = Query(..., description="e.g. 2025-2026"),
) -> Any:
    """
    Get aggregated income and TDS summary for a specific financial year.
    """
    return crud_income_entry.get_summary_by_fy(
        db=db, user_id=current_user.id, financial_year=financial_year
    )
