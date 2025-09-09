import logging
import uuid
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import config, dependencies
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


def _trigger_ppf_recalculation(
    db: Session, *, asset: models.Asset, transaction_date: date
):
    """
    Deletes all future and current year's interest credits for a PPF account
    to trigger a recalculation on the next holdings view.
    """
    if asset.asset_type != "PPF":
        return

    fy_start_year = (
        transaction_date.year
        if transaction_date.month > 3
        else transaction_date.year - 1
    )
    fy_start_date = date(fy_start_year, 4, 1)

    (
        db.query(models.Transaction)
        .filter(
            models.Transaction.asset_id == asset.id,
            models.Transaction.transaction_type == "INTEREST_CREDIT",
            models.Transaction.transaction_date >= fy_start_date,
        )
        .delete(synchronize_session=False)
    )
    logger.info(
        (
            f"Triggered PPF recalculation for asset {asset.id} "
            f"from FY starting {fy_start_date}"
        )
    )


@router.get("/", response_model=schemas.TransactionsResponse)
def read_transactions(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: Optional[uuid.UUID] = None,
    asset_id: Optional[uuid.UUID] = None,
    transaction_type: Optional[str] = Query(None, enum=["BUY", "SELL"]),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
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
        transactions, total = crud.transaction.get_multi_by_user_with_filters(
            db=db, user_id=current_user.id, portfolio_id=None, skip=skip, limit=limit
        )
    if config.settings.DEBUG:
        print("--- BACKEND DEBUG: Read Transactions Response ---")
        if transactions:
            try:
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
    transaction_in: schemas.TransactionCreateWithTicker,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new transaction for a portfolio.
    If the asset does not exist, it will be created.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset_to_use = None
    asset_id_to_use = getattr(transaction_in, "asset_id", None)
    if asset_id_to_use:
        asset_to_use = crud.asset.get(db, id=asset_id_to_use)
    elif getattr(transaction_in, "ticker_symbol", None):
        asset_to_use = crud.asset.get_or_create_by_ticker(
            db,
            ticker_symbol=transaction_in.ticker_symbol,
            asset_type=transaction_in.asset_type,
        )

    if not asset_to_use:
        raise HTTPException(status_code=422, detail="Could not find or create asset.")

    asset_id_to_use = asset_to_use.id

    transaction_create_schema = schemas.TransactionCreate(
        asset_id=asset_id_to_use,
        **transaction_in.model_dump(
            exclude={"ticker_symbol", "asset_type", "asset_id"}
        ),
    )

    try:
        transaction = crud.transaction.create_with_portfolio(
            db=db, obj_in=transaction_create_schema, portfolio_id=portfolio_id
        )
        _trigger_ppf_recalculation(
            db, asset=asset_to_use, transaction_date=transaction.transaction_date.date()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    db.refresh(transaction)
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
    transaction = crud.transaction.get(db=db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.portfolio_id != portfolio_id:
        raise HTTPException(
            status_code=404, detail="Transaction not found in this portfolio"
        )
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # We pass the original transaction date to handle cases where the date
    # itself is changed.
    _trigger_ppf_recalculation(
        db,
        asset=transaction.asset,
        transaction_date=transaction.transaction_date.date(),
    )

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
    transaction = crud.transaction.get(db=db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.portfolio_id != portfolio_id:
        raise HTTPException(
            status_code=404, detail="Transaction not found in this portfolio"
        )
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    _trigger_ppf_recalculation(
        db,
        asset=transaction.asset,
        transaction_date=transaction.transaction_date.date(),
    )

    crud.transaction.remove(db=db, id=transaction_id)
    db.commit()
    return {"msg": "Transaction deleted successfully"}
