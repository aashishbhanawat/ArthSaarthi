from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.crud.base import CRUDBase
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate


class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetUpdate]):
    def get_by_ticker(self, db: Session, *, ticker_symbol: str) -> Asset | None:
        return (
            db.query(self.model).filter(self.model.ticker_symbol == ticker_symbol).first()
        )

    def get_by_isin(self, db: Session, *, isin: str) -> Asset | None:
        return db.query(self.model).filter(self.model.isin == isin).first()

    def search_by_name_or_ticker(self, db: Session, *, query: str) -> List[Asset]:
        search = f"%{query.lower()}%"  # Use wildcards and ensure lowercase for case-insensitive search
        return (
            db.query(self.model)
            .filter(
                or_(
                    func.lower(self.model.name).like(search),
                    func.lower(self.model.ticker_symbol).like(search),
                )
            )
            .limit(10)
            .all()
        )

asset = CRUDAsset(Asset)