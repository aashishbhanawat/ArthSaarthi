import logging
import uuid
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import config, dependencies
from app.crud import crud_corporate_action
from app.crud.crud_ppf import trigger_ppf_recalculation
from app.models.user import User
from app.schemas.enums import TransactionType

router = APIRouter()
logger = logging.getLogger(__name__)


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
        transactions, total = crud.transaction.get_multi_by_user_with_filters(  # type: ignore
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
    transaction_in: schemas.TransactionCreateIn,
    portfolio_id: uuid.UUID = Query(...),
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new transaction for a portfolio, including corporate actions.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset_to_use = None
    if transaction_in.asset_id:
        asset_to_use = crud.asset.get(db, id=transaction_in.asset_id)

    if not asset_to_use and getattr(transaction_in, "ticker_symbol", None):
        asset_to_use = crud.asset.get_or_create_by_ticker(
            db,
            ticker_symbol=transaction_in.ticker_symbol,
            asset_type=transaction_in.asset_type,
        )

    if not asset_to_use:
        raise HTTPException(
            status_code=404,
            detail=(
                "Could not find or create asset with ticker "
                f"'{transaction_in.ticker_symbol}'"
            ),
        )

    asset_id_to_use = asset_to_use.id
    transaction_create_schema = schemas.TransactionCreate(
        asset_id=asset_id_to_use,
        **transaction_in.model_dump(
            exclude={"ticker_symbol", "asset_type", "asset_id"}
        ),
    )

    transaction = None
    transaction_type = transaction_in.transaction_type

    try:
        if transaction_type == TransactionType.DIVIDEND:
            transaction = crud_corporate_action.handle_dividend(
                db=db,
                portfolio_id=portfolio_id,
                asset_id=asset_id_to_use,
                transaction_in=transaction_create_schema,
            )
        elif transaction_type == TransactionType.SPLIT:
            transaction = crud_corporate_action.handle_stock_split(
                db=db,
                portfolio_id=portfolio_id,
                asset_id=asset_id_to_use,
                transaction_in=transaction_create_schema,
            )
        elif transaction_type == TransactionType.BONUS:
            transaction = crud_corporate_action.handle_bonus_issue(
                db=db,
                portfolio_id=portfolio_id,
                asset_id=asset_id_to_use,
                transaction_in=transaction_create_schema,
            )
        else:
            transaction = crud.transaction.create_with_portfolio(
                db=db, obj_in=transaction_create_schema, portfolio_id=portfolio_id
            )
            if asset_to_use.asset_type == "PPF":
                logger.info(
                    "Triggering PPF recalculation for asset %s "
                    "due to new contribution.",
                    asset_to_use.id,
                )
                trigger_ppf_recalculation(db, asset_id=asset_to_use.id)

    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating transaction: {e}", exc_info=True)
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
    if config.settings.DEBUG:
        logger.warning("--- BACKEND DEBUG: Update Transaction Request ---")
        logger.warning(f"Transaction ID: {transaction_id}")
        payload = transaction_in.model_dump_json(indent=2, exclude_unset=True)
        logger.warning(f"Update Payload: {payload}")
        logger.warning("---------------------------------------------")
    transaction = crud.transaction.get(db=db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.portfolio_id != portfolio_id:
        raise HTTPException(
            status_code=404, detail="Transaction not found in this portfolio"
        )
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # --- Smart Recalculation for PPF ---
    if transaction.asset.asset_type == "PPF":
        logger.info(f"Triggering PPF recalculation for asset {transaction.asset_id} "
                    f"due to transaction update."
        )
        trigger_ppf_recalculation(db, asset_id=transaction.asset_id)
    # --- End Smart Recalculation ---

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
        logger.warning("--- BACKEND DEBUG: Delete Transaction Request ---")
        logger.warning(f"Transaction ID: {transaction_id}")
        logger.warning("---------------------------------------------")
    transaction = crud.transaction.get(db=db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.portfolio_id != portfolio_id:
        raise HTTPException(
            status_code=404, detail="Transaction not found in this portfolio"
        )
    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # --- Smart Recalculation for PPF ---
    if transaction.asset.asset_type == "PPF":
        logger.info(f"Triggering PPF recalculation for asset {transaction.asset_id} "
                    f"due to transaction deletion."
        )
        trigger_ppf_recalculation(db, asset_id=transaction.asset_id)
    # --- End Smart Recalculation ---

    crud.transaction.remove(db=db, id=transaction_id)
    db.commit()
    return {"msg": "Transaction deleted successfully"}
