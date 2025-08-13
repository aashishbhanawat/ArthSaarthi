import uuid
from typing import List

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.asset import Asset
from app.models.transaction import Transaction
from app.schemas.asset import AssetCreate, AssetUpdate


class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetUpdate]):
    def get_multi_by_portfolio(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> List[Asset]:
        """
        Retrieves all assets that have at least one transaction in the
        specified portfolio.
         """
        # Get distinct asset_ids from transactions for the given portfolio
        asset_ids_query = (
            db.query(Transaction.asset_id)
            .filter(Transaction.portfolio_id == portfolio_id)
            .distinct()
        )
        asset_ids = [item[0] for item in asset_ids_query.all()]

        if not asset_ids:
            return []

        # Fetch the Asset objects corresponding to these IDs
        return db.query(self.model).filter(self.model.id.in_(asset_ids)).all()
    def get_by_ticker(self, db: Session, *, ticker_symbol: str) -> Asset | None:
        return (
            db.query(self.model)
            .filter(self.model.ticker_symbol == ticker_symbol)
            .first()
        )

    def get_by_isin(self, db: Session, *, isin: str) -> Asset | None:
        return db.query(self.model).filter(self.model.isin == isin).first()

    def search_by_name_or_ticker(self, db: Session, *, query: str) -> List[Asset]:
        # Use wildcards and ensure lowercase for case-insensitive search.
        search = f"%{query.lower()}%"
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
