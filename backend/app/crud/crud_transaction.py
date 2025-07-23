from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud
from app.crud.base import CRUDBase
from app.crud import crud_asset
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def create_with_portfolio(
        self, db: Session, *, obj_in: TransactionCreate, portfolio_id: int
    ) -> Transaction:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        user_id = portfolio.user_id

        # --- New Validation Logic ---
        if obj_in.transaction_type.lower() == "sell":
            if obj_in.new_asset:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot execute a 'SELL' transaction for a new, unrecorded asset.",
                )

            if not obj_in.asset_id:
                raise HTTPException(
                    status_code=400,
                    detail="asset_id is required for a 'SELL' transaction.",
                )

            transactions = (
                db.query(Transaction)
                .filter(
                    Transaction.user_id == user_id,
                    Transaction.asset_id == obj_in.asset_id,
                    Transaction.transaction_date < obj_in.transaction_date,
                )
                .all()
            )

            current_holdings = sum(
                t.quantity if t.transaction_type.lower() == "buy" else -t.quantity
                for t in transactions
            )

            if obj_in.quantity > current_holdings:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient holdings to sell. Current holdings: {current_holdings}, trying to sell: {obj_in.quantity}.",
                )
        # --- End Validation Logic ---
        asset_id = obj_in.asset_id
        if obj_in.new_asset:
            existing_asset = crud_asset.asset.get_by_ticker(
                db, ticker_symbol=obj_in.new_asset.ticker_symbol
            )
            if existing_asset:
                asset_id = existing_asset.id
            else:
                new_asset = crud_asset.asset.create(db, obj_in=obj_in.new_asset)
                asset_id = new_asset.id

        db_obj = Transaction(
            **obj_in.model_dump(exclude={"new_asset", "asset_id"}),
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            user_id=user_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


transaction = CRUDTransaction(Transaction)