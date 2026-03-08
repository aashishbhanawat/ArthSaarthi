import uuid
from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.recurring_deposit import RecurringDeposit
from app.schemas.recurring_deposit import (
    RecurringDepositCreate,
    RecurringDepositUpdate,
)


class CRUDRD(
    CRUDBase[RecurringDeposit, RecurringDepositCreate, RecurringDepositUpdate]
):
    def create_with_portfolio(
        self,
        db: Session,
        *,
        obj_in: RecurringDepositCreate,
        user_id: uuid.UUID,
    ) -> RecurringDeposit:
        db_obj = self.model(
            **obj_in.model_dump(), user_id=user_id
        )
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_portfolio(
        self, db: Session, *, portfolio_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[RecurringDeposit]:
        return (
            db.query(self.model)
            .filter(RecurringDeposit.portfolio_id == portfolio_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


recurring_deposit = CRUDRD(RecurringDeposit)
