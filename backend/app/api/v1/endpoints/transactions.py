import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import config, dependencies
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=schemas.TransactionsResponse)
def read_transactions(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: Optional[uuid.UUID] = None,
    asset_id: Optional[uuid.UUID] = None,
    transaction_type: Optional[str] = Query(None, enum=["BUY", "SELL"]),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Retrieve transactions for the current user, with optional filters.
    """
    if portfolio_id:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if portfolio.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        transactions, total = crud.transaction.get_multi_by_user_with_filters(
            db=db,
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
    else:
        # If no portfolio_id is provided, use the same filter function
        # to fetch all transactions for the user.
        transactions, total = crud.transaction.get_multi_by_user_with_filters( # type: ignore
            db=db, user_id=current_user.id, portfolio_id=None, skip=skip, limit=limit
        )
    if config.settings.DEBUG:
        print("--- BACKEND DEBUG: Read Transactions Response ---")
        # Log the first transaction to see its structure
        if transactions:
            try:
                # Directly accessing attributes from the SQLAlchemy model
                print(f"First transaction ID: {transactions[0].id}")
                print(f"First transaction Portfolio ID: {transactions[0].portfolio_id}")
            except Exception as e:
                print(f"Could not log transaction details: {e}")
        else:
            print("No transactions found to log.")
        print("---------------------------------------------")
    return {"transactions": transactions, "total": total}


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
