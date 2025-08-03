from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import dependencies
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=schemas.Transaction, status_code=201)
def create_transaction(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    transaction_in: schemas.TransactionCreate,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new transaction for a portfolio.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        transaction = crud.transaction.create_with_portfolio(
            db=db, obj_in=transaction_in, portfolio_id=portfolio_id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        # Catch potential database or other internal errors
        raise HTTPException(status_code=400, detail=str(e))

    return transaction
