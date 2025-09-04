from typing import List
import uuid

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.fixed_deposit import FixedDeposit
from app.schemas.fixed_deposit import FixedDepositCreate, FixedDepositUpdate


class CRUDFixedDeposit(CRUDBase[FixedDeposit, FixedDepositCreate, FixedDepositUpdate]):
    def create_with_portfolio(
        self, db: Session, *, obj_in: FixedDepositCreate, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> FixedDeposit:
        db_obj = self.model(**obj_in.dict(), portfolio_id=portfolio_id, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_portfolio(
        self, db: Session, *, portfolio_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[FixedDeposit]:
        return (
            db.query(self.model)
            .filter(FixedDeposit.portfolio_id == portfolio_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


fixed_deposit = CRUDFixedDeposit(FixedDeposit)
