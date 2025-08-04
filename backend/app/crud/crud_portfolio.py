from typing import List
from sqlalchemy.orm import Session
import uuid

from app.crud.base import CRUDBase
from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate


class CRUDPortfolio(CRUDBase[Portfolio, PortfolioCreate, PortfolioUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: PortfolioCreate, user_id: uuid.UUID
    ) -> Portfolio:
        db_obj = Portfolio(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Portfolio]:
        return (
            db.query(self.model)
            .filter(Portfolio.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


portfolio = CRUDPortfolio(Portfolio)