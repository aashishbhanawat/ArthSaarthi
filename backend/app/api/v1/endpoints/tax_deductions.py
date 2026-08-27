import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import dependencies
from app.crud.crud_tax_deduction import crud_tax_deduction

router = APIRouter()


@router.get("", response_model=List[schemas.TaxDeductionResponse])
@router.get("/", response_model=List[schemas.TaxDeductionResponse])
def read_tax_deductions(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
    financial_year: Optional[str] = Query(None, description="e.g. 2025-2026"),
    section: Optional[str] = Query(None, description="e.g. 80C, 80D"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve tax deduction entries for the current user.
    """
    entries = crud_tax_deduction.get_multi_by_owner(
        db=db,
        user_id=current_user.id,
        financial_year=financial_year,
        section=section,
        skip=skip,
        limit=limit,
    )
    result = []
    for entry in entries:
        result.append({
            "id": entry.id,
            "user_id": entry.user_id,
            "financial_year": entry.financial_year,
            "section": entry.section,
            "title": entry.title,
            "amount": entry.amount,
            "deduction_date": entry.deduction_date,
            "proof_notes": entry.proof_notes,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        })
    return result


@router.post("", response_model=schemas.TaxDeductionResponse, status_code=201)
@router.post("/", response_model=schemas.TaxDeductionResponse, status_code=201)
def create_tax_deduction(
    *,
    db: Session = Depends(dependencies.get_db),
    deduction_in: schemas.TaxDeductionCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create a new tax deduction entry.
    """
    entry = crud_tax_deduction.create_with_owner(
        db=db, obj_in=deduction_in, user_id=current_user.id
    )
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "financial_year": entry.financial_year,
        "section": entry.section,
        "title": entry.title,
        "amount": entry.amount,
        "deduction_date": entry.deduction_date,
        "proof_notes": entry.proof_notes,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


@router.get("/summary", response_model=schemas.TaxDeductionFYSummary)
def get_tax_deductions_summary(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
    financial_year: str = Query(..., description="e.g. 2025-2026"),
) -> Any:
    """
    Get aggregated statutory limit summary and eligible tax deductions
    for a financial year.
    """

    return crud_tax_deduction.get_summary_by_fy(
        db=db, user_id=current_user.id, financial_year=financial_year
    )


@router.put("/{deduction_id}", response_model=schemas.TaxDeductionResponse)
def update_tax_deduction(
    *,
    db: Session = Depends(dependencies.get_db),
    deduction_id: uuid.UUID,
    deduction_in: schemas.TaxDeductionUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update an existing tax deduction entry.
    """
    entry = crud_tax_deduction.get_by_id_and_owner(
        db=db, id=deduction_id, user_id=current_user.id
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Tax deduction entry not found")

    updated = crud_tax_deduction.update_with_owner(
        db=db, db_obj=entry, obj_in=deduction_in
    )
    return {
        "id": updated.id,
        "user_id": updated.user_id,
        "financial_year": updated.financial_year,
        "section": updated.section,
        "title": updated.title,
        "amount": updated.amount,
        "deduction_date": updated.deduction_date,
        "proof_notes": updated.proof_notes,
        "created_at": updated.created_at,
        "updated_at": updated.updated_at,
    }


@router.delete("/{deduction_id}", response_model=schemas.TaxDeductionResponse)
def delete_tax_deduction(
    *,
    db: Session = Depends(dependencies.get_db),
    deduction_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a tax deduction entry.
    """
    entry = crud_tax_deduction.get_by_id_and_owner(
        db=db, id=deduction_id, user_id=current_user.id
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Tax deduction entry not found")

    res_dict = {
        "id": entry.id,
        "user_id": entry.user_id,
        "financial_year": entry.financial_year,
        "section": entry.section,
        "title": entry.title,
        "amount": entry.amount,
        "deduction_date": entry.deduction_date,
        "proof_notes": entry.proof_notes,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }
    crud_tax_deduction.remove(db=db, id=deduction_id)
    db.commit()
    return res_dict
