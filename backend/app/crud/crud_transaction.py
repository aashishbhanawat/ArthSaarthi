from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.crud import crud_asset
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def create_with_portfolio(
        self, db: Session, *, obj_in: TransactionCreate, portfolio_id: int
    ) -> Transaction:
        portfolio = crud.portfolio.get(db, id=portfolio_id)
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
            user_id=portfolio.user_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


transaction = CRUDTransaction(Transaction)