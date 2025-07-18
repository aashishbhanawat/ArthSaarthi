from typing import List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.crud import crud_asset
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionCreateInternal


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def create_with_asset_handling(
        self, db: Session, *, obj_in: TransactionCreate, user_id: int
    ) -> Transaction:
        # Handle asset creation or retrieval
        asset_id = obj_in.asset_id
        if obj_in.new_asset:
            # Check if asset with ticker already exists
            existing_asset = crud_asset.asset.get_by_ticker(db, ticker_symbol=obj_in.new_asset.ticker_symbol)
            if existing_asset:
                asset_id = existing_asset.id
            else:
                # Create new asset
                new_asset = crud_asset.asset.create(db, obj_in=obj_in.new_asset)
                asset_id = new_asset.id

        # Create the internal transaction object with the definite asset_id
        transaction_internal_data = TransactionCreateInternal(
            **obj_in.dict(exclude={'asset_id', 'new_asset'}),
            asset_id=asset_id
        )

        db_obj = self.model(**transaction_internal_data.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(self, db: Session, *, user_id: int) -> List[Transaction]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()


transaction = CRUDTransaction(Transaction)