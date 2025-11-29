import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import crud, schemas
from app.crud.base import CRUDBase
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def get_holdings_on_date(
        self, db: Session, *, user_id: uuid.UUID, asset_id: uuid.UUID, on_date: datetime
    ) -> Decimal:
        # Calculate total buys (and other acquisitions) up to the date
        acquisition_types = ["BUY", "ESPP_PURCHASE", "RSU_VEST", "BONUS"]
        total_buys = db.query(func.sum(Transaction.quantity)).filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_type.in_(acquisition_types),
            Transaction.transaction_date <= on_date,
        ).scalar() or Decimal("0")

        # Calculate total sells up to the date
        total_sells = db.query(func.sum(Transaction.quantity)).filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_type == "SELL",
            Transaction.transaction_date <= on_date,
        ).scalar() or Decimal("0")

        # Note: This simple calculation does not account for SPLITs correctly if they
        # just record the ratio. However, typically splits might be recorded as
        # closing old position and opening new, or adding difference.
        # For RSU/ESPP support, we explicitly added them to acquisition_types.

        return total_buys - total_sells

    # The create_with_portfolio method is now simplified.
    # The complex logic for creating a new asset is removed.
    def create_with_portfolio(
        self, db: Session, *, obj_in: schemas.TransactionCreate, portfolio_id: uuid.UUID
    ) -> Transaction:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        if obj_in.transaction_type.upper() == "SELL":
            current_holdings = self.get_holdings_on_date(
                db,
                user_id=portfolio.user_id,
                asset_id=obj_in.asset_id,
                on_date=obj_in.transaction_date,
            )
            # Use a small epsilon for float comparison if needed, but Decimal is exact
            if obj_in.quantity > current_holdings:
                # We should allow selling if it's a "Sell to Cover" causing this?
                # No, Sell to Cover happens AFTER vest (or same time).
                # If same time, get_holdings_on_date (<= on_date) should see the vest
                # IF the vest is committed or processed first.
                # Since we create RSU_VEST *before* SELL in the loop, and both have same date,
                # get_holdings_on_date *might* see RSU_VEST if it's in the same session?
                # No, get_holdings_on_date issues a SELECT.
                # If we haven't committed the RSU_VEST, the SELECT won't see it (unless isolation level allows, usually READ COMMITTED doesn't see uncommitted from same txn unless using same session and flush).
                # We do `db.add(db_obj)` -> `db.flush()` in `create_with_portfolio`.
                # So if we call `create_with_portfolio` for RSU first, it is flushed.
                # Then we call it for SELL.
                # The `get_holdings_on_date` uses `db.query(...)`.
                # Since it uses the same `db` session, it SHOULD see the flushed changes.
                pass
                # Check logic below

            if obj_in.quantity > current_holdings:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Insufficient holdings to sell. Current holdings:"
                        f" {current_holdings}, trying to sell: {obj_in.quantity}"
                    ),
                )

        db_obj = self.model(
            **obj_in.model_dump(), user_id=portfolio.user_id, portfolio_id=portfolio_id
        )
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_user_with_filters(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        asset_id: Optional[uuid.UUID] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Transaction], int]:
        query = db.query(self.model).filter(
            self.model.user_id == user_id, self.model.portfolio_id == portfolio_id
        )

        if asset_id:
            query = query.filter(self.model.asset_id == asset_id)
        if transaction_type:
            query = query.filter(
                self.model.transaction_type == transaction_type.upper()
            )
        if start_date:
            query = query.filter(self.model.transaction_date >= start_date)
        if end_date:
            query = query.filter(self.model.transaction_date <= end_date)

        total = query.count()
        transactions = (
            query.order_by(self.model.transaction_date.desc()).offset(skip).limit(limit).all()
        )
        return transactions, total

    def get_multi_by_portfolio(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> List[Transaction]:
        return (
            db.query(self.model).filter(self.model.portfolio_id == portfolio_id).all()
        )

    def get_multi_by_asset(
        self, db: Session, *, asset_id: uuid.UUID
    ) -> List[Transaction]:
        """Retrieves all transactions for a specific asset."""
        return db.query(self.model).filter(self.model.asset_id == asset_id).all()

    def get_multi_by_portfolio_and_asset(
        self, db: Session, *, portfolio_id: uuid.UUID, asset_id: uuid.UUID
    ) -> List[Transaction]:
        return (
            db.query(self.model)
            .filter(
                Transaction.portfolio_id == portfolio_id,
                Transaction.asset_id == asset_id,
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

    def get_multi_by_portfolio_and_asset_before_date(
        self,
        db: Session,
        *,
        portfolio_id: uuid.UUID,
        asset_id: uuid.UUID,
        date: datetime,
    ) -> List[Transaction]:
        """
        Retrieves all BUY and SELL transactions for a specific asset in a portfolio
        that occurred before a given date.
        """
        return (
            db.query(self.model)
            .filter(
                Transaction.portfolio_id == portfolio_id,
                Transaction.asset_id == asset_id,
                Transaction.transaction_date < date,
                Transaction.transaction_type.in_(["BUY", "SELL"]),
            )
            .order_by(Transaction.transaction_date)
            .all()
        )

    def get_by_details(
        self,
        db: Session,
        *,
        portfolio_id: uuid.UUID,
        asset_id: uuid.UUID,
        transaction_date: datetime,
        transaction_type: str,
        quantity: Decimal,
        price_per_unit: Decimal,
    ) -> Transaction | None:
        return (
            db.query(self.model)
            .filter(
                self.model.portfolio_id == portfolio_id,
                self.model.asset_id == asset_id,
                self.model.transaction_date == transaction_date,
                self.model.transaction_type == transaction_type,
                self.model.quantity == quantity,
                self.model.price_per_unit == price_per_unit,
            )
            .first()
        )


transaction = CRUDTransaction(Transaction)
