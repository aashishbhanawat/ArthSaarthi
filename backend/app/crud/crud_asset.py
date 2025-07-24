from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_

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

    def search_by_name_or_ticker(
        self, db: Session, *, query: str, limit: int = 10
    ) -> List[Asset]:
        query_str = f"%{query.lower()}%"
        return (
            db.query(self.model)
            .filter(
                or_(
                    self.model.ticker_symbol.ilike(query_str),
                    self.model.name.ilike(query_str),
                )
            )
            .limit(limit)
            .all()
        )

asset = CRUDAsset(Asset)