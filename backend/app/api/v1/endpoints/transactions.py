from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core import dependencies as deps
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=schemas.Transaction, status_code=201)
def create_transaction(
    *,
    db: Session = Depends(deps.get_db),
    portfolio_id: int,
    transaction_in: schemas.TransactionCreate,
    current_user: User = Depends(deps.get_current_user),
):
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    transaction = crud.transaction.create_with_portfolio(
        db=db, obj_in=transaction_in, portfolio_id=portfolio_id
    )
    return transaction