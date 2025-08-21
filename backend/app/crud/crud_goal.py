import uuid
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.goal import Goal, GoalLink
from app.schemas.goal import GoalCreate, GoalLinkCreate, GoalLinkUpdate, GoalUpdate


class CRUDGoal(CRUDBase[Goal, GoalCreate, GoalUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: GoalCreate, user_id: uuid.UUID
    ) -> Goal:
        db_obj = self.model(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Goal]:
        return (
            db.query(self.model)
            .filter(Goal.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_goal_progress(self, db: Session, *, goal_id: uuid.UUID) -> Decimal:
        goal = self.get(db, id=goal_id)
        if not goal:
            return Decimal(0)

        total_value = Decimal(0)
        for link in goal.links:
            if link.portfolio_id:
                summary = crud.holding.get_portfolio_holdings_and_summary(
                    db, portfolio_id=link.portfolio_id
                )["summary"]
                total_value += summary.total_value
            # Not implementing single asset linking for now
            # else if link.asset_id:
            #     pass
        return total_value


class CRUDGoalLink(CRUDBase[GoalLink, GoalLinkCreate, GoalLinkUpdate]):
    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: GoalLinkCreate,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
    ) -> GoalLink:
        db_obj = self.model(**obj_in.model_dump(), user_id=user_id, goal_id=goal_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


goal = CRUDGoal(Goal)
goal_link = CRUDGoalLink(GoalLink)
