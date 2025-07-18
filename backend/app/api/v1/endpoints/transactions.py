from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=schemas.Transaction, status_code=201)
def create_transaction(
    *,
    db: Session = Depends(dependencies.get_db),
    transaction_in: schemas.TransactionCreate,
    current_user: User = Depends(dependencies.get_current_user),
):
    """
    Create new transaction.

    This endpoint handles both creating a transaction for an existing asset
    and creating a new asset if one is provided in the payload.
    """
    # Check if the portfolio belongs to the current user
    portfolio = crud.portfolio.get(db=db, id=transaction_in.portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # If an existing asset is being used, check if it's valid
    if transaction_in.asset_id:
        asset = crud.asset.get(db=db, id=transaction_in.asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

    transaction = crud.transaction.create_with_asset_handling(
        db=db, obj_in=transaction_in, user_id=current_user.id
    )
    return transaction