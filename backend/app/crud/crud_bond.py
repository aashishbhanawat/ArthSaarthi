from uuid import UUID

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.bond import Bond
from app.schemas.bond import BondCreate, BondUpdate


class CRUDBond(CRUDBase[Bond, BondCreate, BondUpdate]):
    def get_by_asset_id(self, db: Session, *, asset_id: UUID) -> Bond | None:
        """
        Gets a Bond record by its associated asset_id.
        """
        return db.query(self.model).filter(self.model.asset_id == asset_id).first()


bond = CRUDBond(Bond)
