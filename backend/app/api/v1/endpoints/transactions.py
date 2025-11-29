import logging
import uuid
from datetime import date
from typing import Any, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.cache.utils import invalidate_caches_for_portfolio
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


@router.post("/", response_model=schemas.TransactionCreatedResponse, status_code=201)
def create_transaction(
    *,
    db: Session = Depends(dependencies.get_db),
    transactions_in: Union[
        schemas.TransactionCreateIn, List[schemas.TransactionCreateIn]
    ],
    portfolio_id: uuid.UUID = Query(...),
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create one or more new transactions for a portfolio.
    """
    logger.debug("create trasaction request received")
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not isinstance(transactions_in, list):
        transactions_in = [transactions_in]

    created_transactions = []

    try:
        for transaction_in in transactions_in:
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

            transaction_type = transaction_in.transaction_type

            # Check for RSU "Sell to Cover"
            if transaction_type == TransactionType.RSU_VEST and transaction_in.details:
                sell_to_cover = transaction_in.details.get("sell_to_cover")
                # Ensure sell_to_cover is a dict and has valid data
                if sell_to_cover and isinstance(sell_to_cover, dict):
                    # 1. Create RSU VEST Transaction (main one)
                    transaction = crud.transaction.create_with_portfolio(
                        db=db, obj_in=transaction_create_schema, portfolio_id=portfolio_id
                    )
                    created_transactions.append(transaction)

                    # 2. Create SELL Transaction
                    # Extract fields, defaulting to main txn date if not specified (it shouldn't be for sell to cover usually)
                    sell_qty = sell_to_cover.get("quantity")
                    sell_price = sell_to_cover.get("price_per_unit")

                    if sell_qty is not None and sell_price is not None:
                         sell_details = {"related_rsu_vest_id": str(transaction.id)}
                         sell_tx_schema = schemas.TransactionCreate(
                             asset_id=asset_id_to_use,
                             transaction_type=TransactionType.SELL,
                             quantity=sell_qty,
                             price_per_unit=sell_price,
                             transaction_date=transaction_create_schema.transaction_date,
                             fees=0, # Assuming 0 fees for auto-sell unless specified, keeping simple
                             details=sell_details
                         )
                         sell_transaction = crud.transaction.create_with_portfolio(
                            db=db, obj_in=sell_tx_schema, portfolio_id=portfolio_id
                         )
                         created_transactions.append(sell_transaction)

                    # Skip default creation since we handled it
                    if asset_to_use.asset_type == "PPF":
                        trigger_ppf_recalculation(db, asset_id=asset_to_use.id)
                    continue

            # Standard logic
            is_reinvested_dividend = (
                transaction_type == TransactionType.DIVIDEND
                and getattr(transaction_in, "is_reinvested", False) is True
            )
            logger.debug(f"Is reinvested dividend? {is_reinvested_dividend}")
            if is_reinvested_dividend:  # noqa: E501
                logger.info(
                    "Handling reinvested dividend via corporate action handler "
                    "for asset %s.",
                    asset_id_to_use,
                )
                logger.debug(
                    "Full incoming payload for reinvestment: %s",
                    transaction_in.model_dump_json(indent=2),
                )
                transaction = crud_corporate_action.handle_dividend(
                    db=db,
                    portfolio_id=portfolio_id,
                    asset_id=asset_id_to_use,
                    transaction_in=transaction_in,
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
                logger.debug(
                    "else part of create transaction logic for %s", transaction_type
                )
                transaction = crud.transaction.create_with_portfolio(
                    db=db, obj_in=transaction_create_schema, portfolio_id=portfolio_id
                )
                if asset_to_use.asset_type == "PPF":
                    trigger_ppf_recalculation(db, asset_id=asset_to_use.id)

            created_transactions.append(transaction)

    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating transaction: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

    # Commit all changes at once to ensure transactional integrity
    db.commit()

    # Invalidate caches after successful commit
    invalidate_caches_for_portfolio(db, portfolio_id=portfolio_id)

    return {"created_transactions": created_transactions}


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

    # Invalidate cache after successful update
    invalidate_caches_for_portfolio(db, portfolio_id=portfolio_id)

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

    # Invalidate cache after successful deletion
    invalidate_caches_for_portfolio(db, portfolio_id=portfolio_id)

    return {"msg": "Transaction deleted successfully"}
