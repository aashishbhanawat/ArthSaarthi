import logging
import uuid
import uuid as uuid_module
from datetime import date, datetime
from decimal import Decimal
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
from app.utils.pydantic_compat import model_dump, model_dump_json

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
    if portfolio_id and not asset_id and not transaction_type:
        all_fds = crud.fixed_deposit.get_multi_by_portfolio(
            db, portfolio_id=portfolio_id
        )

        today = date.today()
        for fd in all_fds:
            # Build a lightweight synthetic asset so the row renders properly
            dummy_asset = models.Asset(
                id=fd.id,
                ticker_symbol=fd.account_number or f"FD-{fd.id}",
                name=fd.name,
                asset_type="FIXED_DEPOSIT",
                currency="INR",
                exchange="N/A",
            )

            # Derive a stable distinct UUID for the deposit row
            # (namespace off the fd id)
            deposit_uuid = uuid_module.uuid5(fd.id, "deposit")
            fd_id_str = str(fd.id)

            # 1️⃣  FD_DEPOSIT entry – initial principal on start_date (all FDs, read-only)
            start_dt = datetime.combine(fd.start_date, datetime.min.time())
            buy_tx = models.Transaction(
                id=deposit_uuid,
                transaction_type="FD_DEPOSIT",
                quantity=fd.principal_amount,
                price_per_unit=Decimal("1.0"),
                fees=Decimal("0.0"),
                is_reinvested=False,
                transaction_date=start_dt,
                portfolio_id=fd.portfolio_id,
                asset_id=fd.id,
                user_id=current_user.id,
                details={"_fd_id": fd_id_str},
            )
            buy_tx.asset = dummy_asset
            transactions.append(buy_tx)
            total += 1

            # 2️⃣  FD_MATURITY entry – maturity payout
            # (matured FDs only, deletable → deletes the FD record)
            if fd.maturity_date <= today:
                maturity_dt = datetime.combine(fd.maturity_date, datetime.min.time())
                sell_tx = models.Transaction(
                    id=fd.id,
                    transaction_type="FD_MATURITY",
                    quantity=fd.principal_amount,
                    price_per_unit=Decimal("1.0"),
                    fees=Decimal("0.0"),
                    is_reinvested=False,
                    transaction_date=maturity_dt,
                    portfolio_id=fd.portfolio_id,
                    asset_id=fd.id,
                    user_id=current_user.id,
                    details={"_fd_id": fd_id_str},
                )
                sell_tx.asset = dummy_asset
                transactions.append(sell_tx)
                total += 1

        # Normalise tz-awareness before sorting
        # (DB rows are naive; synthetic are naive too now)
        transactions.sort(
            key=lambda t: t.transaction_date.replace(tzinfo=None),
            reverse=True,
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


@router.get("/available-lots/{asset_id}", response_model=List[dict])
def get_available_lots(
    *,
    db: Session = Depends(dependencies.get_db),
    asset_id: uuid.UUID,
    exclude_transaction_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get available lots for a specific asset to support specific identification logic.
    """
    # Verify asset belongs to user's portfolio implicitly by checking user_id
    # Actually availability depends on user + asset.
    return crud.transaction.get_available_lots(
        db=db,
        user_id=current_user.id,
        asset_id=asset_id,
        exclude_sell_id=exclude_transaction_id,
    )


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
                **model_dump(transaction_in,
                    exclude={"ticker_symbol", "asset_type", "asset_id"}
                ),
            )

            transaction_type = transaction_in.transaction_type

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
                    model_dump_json(transaction_in, indent=2),
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
                created_transactions.append(transaction)
            elif transaction_type == TransactionType.BONUS:
                transaction = crud_corporate_action.handle_bonus_issue(
                    db=db,
                    portfolio_id=portfolio_id,
                    asset_id=asset_id_to_use,
                    transaction_in=transaction_create_schema,
                )
                created_transactions.append(transaction)
            elif transaction_type == TransactionType.MERGER:
                transaction = crud_corporate_action.handle_merger(
                    db=db,
                    portfolio_id=portfolio_id,
                    asset_id=asset_id_to_use,
                    transaction_in=transaction_create_schema,
                )
                created_transactions.append(transaction)
            elif transaction_type == TransactionType.DEMERGER:
                transaction = crud_corporate_action.handle_demerger(
                    db=db,
                    portfolio_id=portfolio_id,
                    asset_id=asset_id_to_use,
                    transaction_in=transaction_create_schema,
                )
                created_transactions.append(transaction)
            elif transaction_type == TransactionType.RENAME:
                transaction = crud_corporate_action.handle_rename(
                    db=db,
                    portfolio_id=portfolio_id,
                    asset_id=asset_id_to_use,
                    transaction_in=transaction_create_schema,
                )
                created_transactions.append(transaction)
            else:
                logger.debug(
                    "else part of create transaction logic for %s", transaction_type
                )
                # create_with_portfolio can return multiple transactions (e.g., RSU +
                # Sell to Cover)
                newly_created = crud.transaction.create_with_portfolio(
                    db=db, obj_in=transaction_create_schema, portfolio_id=portfolio_id
                )
                if isinstance(newly_created, list):
                    created_transactions.extend(newly_created)
                else:
                    created_transactions.append(newly_created)

                if asset_to_use and asset_to_use.asset_type == "PPF":
                    trigger_ppf_recalculation(db, asset_id=asset_to_use.id)
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=400, detail="An error occurred while creating the transaction."
        )

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
        payload = model_dump_json(transaction_in, indent=2, exclude_unset=True)
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
