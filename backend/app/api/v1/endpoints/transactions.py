import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import config, dependencies
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
    if config.settings.DEBUG:
        print("--- BACKEND DEBUG: Create Transaction Request ---")
        print(f"Portfolio ID: {portfolio_id}")
        print(f"Transaction Payload: {transaction_in.model_dump_json(indent=2)}")
        print("---------------------------------------------")
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

    db.commit()
    return transaction


@router.put("/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    transaction_id: uuid.UUID,
    transaction_in: schemas.TransactionUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update a transaction.
    """
    if config.settings.DEBUG:
        print("--- BACKEND DEBUG: Update Transaction Request ---")
        print(f"Transaction ID: {transaction_id}")
        payload = transaction_in.model_dump_json(indent=2, exclude_unset=True)
        print(f"Update Payload: {payload}")
        print("---------------------------------------------")
    transaction = crud.transaction.get(db=db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.portfolio_id != portfolio_id:
        raise HTTPException(
            status_code=404, detail="Transaction not found in this portfolio"
        )
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    updated_transaction = crud.transaction.update(
        db=db, db_obj=transaction, obj_in=transaction_in
    )
    db.commit()
    db.refresh(updated_transaction)
    return updated_transaction


@router.delete("/{transaction_id}", response_model=schemas.Msg)
def delete_transaction(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    transaction_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a transaction.
    """
    if config.settings.DEBUG:
        print("--- BACKEND DEBUG: Delete Transaction Request ---")
        print(f"Transaction ID: {transaction_id}")
        print("---------------------------------------------")
    transaction = crud.transaction.get(db=db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.portfolio_id != portfolio_id:
        raise HTTPException(
            status_code=404, detail="Transaction not found in this portfolio"
        )
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    crud.transaction.remove(db=db, id=transaction_id)
    db.commit()
    return {"msg": "Transaction deleted successfully"}
