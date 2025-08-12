from typing import Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.asset_alias import AssetAlias
from app.schemas.asset_alias import AssetAliasCreate


class CRUDAssetAlias(CRUDBase[AssetAlias, AssetAliasCreate, AssetAliasCreate]):
    def get_by_alias(
        self, db: Session, *, alias_symbol: str
    ) -> Optional[AssetAlias]:
        return (
            db.query(self.model)
            .filter(self.model.alias_symbol == alias_symbol)
            .first()
        )


asset_alias = CRUDAssetAlias(AssetAlias)
