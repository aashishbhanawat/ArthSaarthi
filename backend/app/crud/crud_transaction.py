import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import Date, cast, func
from sqlalchemy.orm import Session

from app import crud, schemas
from app.crud.base import CRUDBase
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def get_holdings_on_date(
        self, db: Session, *, user_id: uuid.UUID, asset_id: uuid.UUID, on_date: datetime
    ) -> Decimal:
        # Calculate total buys up to the date
        total_buys = db.query(func.sum(Transaction.quantity)).filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_type == "BUY",
            Transaction.transaction_date <= on_date,
        ).scalar() or Decimal("0")

        # Calculate total sells up to the date
        total_sells = db.query(func.sum(Transaction.quantity)).filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_type == "SELL",
            Transaction.transaction_date <= on_date,
        ).scalar() or Decimal("0")

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
        return db_obj

    def get_multi_by_portfolio(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> List[Transaction]:
        return (
            db.query(self.model).filter(self.model.portfolio_id == portfolio_id).all()
        )

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

    def get_by_details(
        self,
        db: Session,
        *,
        portfolio_id: uuid.UUID,
        asset_id: uuid.UUID,
        transaction_date: date,
        transaction_type: str,
        quantity: Decimal,
        price_per_unit: Decimal,
    ) -> Transaction | None:
        return (
            db.query(self.model)
            .filter(
                self.model.portfolio_id == portfolio_id,
                self.model.asset_id == asset_id,
                cast(self.model.transaction_date, Date) == transaction_date,
                self.model.transaction_type == transaction_type,
                self.model.quantity == quantity,
                self.model.price_per_unit == price_per_unit,
            )
            .first()
        )


transaction = CRUDTransaction(Transaction)
