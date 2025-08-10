from app.crud.base import CRUDBase
from app.models.asset_alias import AssetAlias
from app.schemas.asset_alias import AssetAliasCreate


class CRUDAssetAlias(CRUDBase[AssetAlias, AssetAliasCreate, AssetAliasCreate]):
    pass


asset_alias = CRUDAssetAlias(AssetAlias)
