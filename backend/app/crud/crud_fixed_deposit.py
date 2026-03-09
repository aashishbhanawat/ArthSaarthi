import uuid
from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.fixed_deposit import FixedDeposit
from app.schemas.fixed_deposit import FixedDepositCreate, FixedDepositUpdate


class CRUDFixedDeposit(CRUDBase[FixedDeposit, FixedDepositCreate, FixedDepositUpdate]):
    def create_with_portfolio(
        self,
        db: Session,
        *,
        obj_in: FixedDepositCreate,
        user_id: uuid.UUID,
    ) -> FixedDeposit:
        # Check for duplicate FD in the same portfolio
        from fastapi import HTTPException
        existing = (
            db.query(self.model)
            .filter(
                self.model.portfolio_id == obj_in.portfolio_id,
                self.model.name == obj_in.name,
                self.model.account_number == obj_in.account_number,
                self.model.start_date == obj_in.start_date,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A fixed deposit with the same name, account number, and start "
                    "date already exists in this portfolio."
                ),
            )

        db_obj = self.model(
            **obj_in.model_dump(), user_id=user_id
        )
        db.add(db_obj)
        db.flush()
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
