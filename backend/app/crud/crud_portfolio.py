from typing import List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate


class CRUDPortfolio(CRUDBase[Portfolio, PortfolioCreate, PortfolioUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: PortfolioCreate, user_id: int
    ) -> Portfolio:
        db_obj = self.model(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(self, db: Session, *, user_id: int) -> List[Portfolio]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()

portfolio = CRUDPortfolio(Portfolio)