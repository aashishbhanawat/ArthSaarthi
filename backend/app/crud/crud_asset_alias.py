from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.crud.base import CRUDBase
from app.models.asset_alias import AssetAlias
from app.schemas.asset_alias import AssetAliasCreate, AssetAliasUpdate


class CRUDAssetAlias(CRUDBase[AssetAlias, AssetAliasCreate, AssetAliasUpdate]):
    def get_by_alias(
        self, db: Session, *, alias_symbol: str, source: str
    ) -> Optional[AssetAlias]:
        return (
            db.query(self.model)
            .filter(
                self.model.alias_symbol == alias_symbol, self.model.source == source
            )
            .first()
        )

    def get_all_with_assets(self, db: Session) -> List[AssetAlias]:
        """Fetch all aliases with eager-loaded asset relationship."""
        return (
            db.query(self.model)
            .options(joinedload(self.model.asset))
            .order_by(self.model.alias_symbol)
            .all()
        )

    def search_with_assets(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AssetAlias], int]:
        """Search aliases with pagination. Returns (items, total_count)."""
        from app.models.asset import Asset

        q = (
            db.query(self.model)
            .outerjoin(Asset, self.model.asset_id == Asset.id)
            .options(joinedload(self.model.asset))
        )
        if query:
            pattern = f"%{query}%"
            q = q.filter(
                self.model.alias_symbol.ilike(pattern)
                | self.model.source.ilike(pattern)
                | Asset.name.ilike(pattern)
                | Asset.ticker_symbol.ilike(pattern)
            )
        total = q.count()
        items = (
            q.order_by(self.model.alias_symbol)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total


asset_alias = CRUDAssetAlias(AssetAlias)
