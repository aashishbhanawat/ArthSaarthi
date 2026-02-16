from typing import List, Optional

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


asset_alias = CRUDAssetAlias(AssetAlias)
