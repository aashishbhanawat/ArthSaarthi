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
from app.schemas.enums import TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def get_holdings_on_date(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
        on_date: datetime,
        include_uncommitted: bool = False,
    ) -> Decimal:
        # Base query for committed transactions
        query = db.query(func.sum(Transaction.quantity)).filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_date <= on_date,
        )

        # Calculate total buys up to the date
        buy_types = [
            TransactionType.BUY,
            TransactionType.RSU_VEST,
            TransactionType.ESPP_PURCHASE,
        ]
        total_buys = (
            query.filter(Transaction.transaction_type.in_(buy_types)).scalar()
            or Decimal("0")
        )

        # Calculate total sells up to the date
        total_sells = (
            query.filter(Transaction.transaction_type == TransactionType.SELL).scalar()
            or Decimal("0")
        )

        uncommitted_buys = Decimal("0")
        if include_uncommitted:
            uncommitted_buys = sum(
                t.quantity
                for t in db.new
                if isinstance(t, Transaction)
                and t.user_id == user_id
                and t.asset_id == asset_id
                and t.transaction_type in buy_types
                and t.transaction_date <= on_date
            )

        return total_buys + uncommitted_buys - total_sells

    def create_with_portfolio(
        self, db: Session, *, obj_in: schemas.TransactionCreate, portfolio_id: uuid.UUID
    ) -> Transaction:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # RSU Vesting Logic
        if obj_in.transaction_type == TransactionType.RSU_VEST:
            if obj_in.price_per_unit != 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RSU vests must have a price of 0.",
                )
            if not obj_in.details or "fmv_at_vest" not in obj_in.details:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RSU vest details must include 'fmv_at_vest'.",
                )

        # ESPP Purchase Logic
        if obj_in.transaction_type == TransactionType.ESPP_PURCHASE:
            if not obj_in.details or "market_price" not in obj_in.details:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ESPP purchase details must include 'market_price'.",
                )

        # Standard SELL transaction validation
        if obj_in.transaction_type == TransactionType.SELL:
            current_holdings = self.get_holdings_on_date(
                db,
                user_id=portfolio.user_id,
                asset_id=obj_in.asset_id,
                on_date=obj_in.transaction_date,
                include_uncommitted=True,
            )
            if obj_in.quantity > current_holdings:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Insufficient holdings to sell. Current holdings:"
                        f" {current_holdings}, trying to sell: {obj_in.quantity}"
                    ),
                )

        # Create the primary transaction
        db_obj = self.model(
            **obj_in.model_dump(), user_id=portfolio.user_id, portfolio_id=portfolio_id
        )
        db.add(db_obj)
        db.flush()

        # "Sell to Cover" Logic
        if (
            obj_in.transaction_type == TransactionType.RSU_VEST
            and obj_in.details
            and "sell_to_cover_shares" in obj_in.details
        ):
            sell_to_cover_shares = Decimal(obj_in.details["sell_to_cover_shares"])
            if sell_to_cover_shares > 0:
                sale_price = Decimal(
                    obj_in.details.get(
                        "sell_to_cover_price", obj_in.details["fmv_at_vest"]
                    )
                )
                sell_transaction = schemas.TransactionCreate(
                    asset_id=obj_in.asset_id,
                    transaction_type=TransactionType.SELL,
                    quantity=sell_to_cover_shares,
                    price_per_unit=sale_price,
                    transaction_date=obj_in.transaction_date,
                    fees=Decimal("0.0"),
                )
                self.create_with_portfolio(
                    db, obj_in=sell_transaction, portfolio_id=portfolio_id
                )

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
