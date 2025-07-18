from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate


class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetUpdate]):
    def get_by_ticker(self, db: Session, *, ticker_symbol: str) -> Asset | None:
        return db.query(self.model).filter(self.model.ticker_symbol == ticker_symbol).first()

    def create(self, db: Session, *, obj_in: AssetCreate) -> Asset:
        # Override create to prevent creating duplicates
        db_obj = self.get_by_ticker(db, ticker_symbol=obj_in.ticker_symbol)
        if db_obj:
            return db_obj

        db_obj = Asset(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

asset = CRUDAsset(Asset)