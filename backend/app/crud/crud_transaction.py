from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.crud.base import CRUDBase
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app import crud, schemas
from fastapi import HTTPException, status


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def get_holdings_on_date(self, db: Session, *, user_id: int, asset_id: int, on_date: str) -> Decimal:
        # Calculate total buys up to the date
        total_buys = db.query(func.sum(Transaction.quantity)).filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_type == 'BUY',
            Transaction.transaction_date <= on_date
        ).scalar() or Decimal('0')

        # Calculate total sells up to the date
        total_sells = db.query(func.sum(Transaction.quantity)).filter(
            Transaction.user_id == user_id,
            Transaction.asset_id == asset_id,
            Transaction.transaction_type == 'SELL',
            Transaction.transaction_date <= on_date
        ).scalar() or Decimal('0')

        return total_buys - total_sells

    def create_with_portfolio(
        self, db: Session, *, obj_in: schemas.TransactionCreate, portfolio_id: int
    ) -> Transaction:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        if obj_in.transaction_type.upper() == 'SELL':
            current_holdings = self.get_holdings_on_date(db, user_id=portfolio.user_id, asset_id=obj_in.asset_id, on_date=obj_in.transaction_date.isoformat())
            if obj_in.quantity > current_holdings:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient holdings to sell. Current holdings: {current_holdings}, trying to sell: {obj_in.quantity}")

        db_obj = self.model(**obj_in.model_dump(), user_id=portfolio.user_id, portfolio_id=portfolio_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


transaction = CRUDTransaction(Transaction)