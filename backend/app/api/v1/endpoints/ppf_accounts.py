from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.cache.utils import invalidate_caches_for_portfolio
from app.core import dependencies

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.Transaction,
    status_code=status.HTTP_201_CREATED,
)
def create_ppf_account(
    *,
    db: Session = Depends(dependencies.get_db),
    ppf_in: schemas.PpfAccountCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create a new PPF account and its first contribution transaction.
    """
    portfolio = crud.portfolio.get(db=db, id=ppf_in.portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Portfolio not found or not owned by user"
        )

    transaction = crud.asset.create_ppf_and_first_contribution(
        db=db, portfolio_id=ppf_in.portfolio_id, ppf_in=ppf_in
    )
    invalidate_caches_for_portfolio(db, portfolio_id=ppf_in.portfolio_id)
    db.commit()
    db.refresh(transaction)
    return transaction
