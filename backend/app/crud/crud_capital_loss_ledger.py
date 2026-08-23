import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.capital_loss_ledger import CapitalLossLedger
from app.schemas.capital_gains import CapitalLossLedgerCreate, CapitalLossLedgerUpdate
from app.utils.pydantic_compat import model_dump


class CRUDCapitalLossLedger(
    CRUDBase[CapitalLossLedger, CapitalLossLedgerCreate, CapitalLossLedgerUpdate]
):
    def create_with_owner(
        self, db: Session, *, obj_in: CapitalLossLedgerCreate, user_id: uuid.UUID
    ) -> CapitalLossLedger:
        db_obj = CapitalLossLedger(**model_dump(obj_in), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_owner_and_ay(
        self, db: Session, *, user_id: uuid.UUID, assessment_year: str
    ) -> Optional[CapitalLossLedger]:
        return (
            db.query(CapitalLossLedger)
            .filter(
                CapitalLossLedger.user_id == user_id,
                CapitalLossLedger.assessment_year == assessment_year,
            )
            .first()
        )

    def get_multi_by_owner(
        self, db: Session, *, user_id: uuid.UUID
    ) -> List[CapitalLossLedger]:
        return (
            db.query(CapitalLossLedger)
            .filter(CapitalLossLedger.user_id == user_id)
            .order_by(CapitalLossLedger.assessment_year.asc())
            .all()
        )


capital_loss_ledger = CRUDCapitalLossLedger(CapitalLossLedger)
