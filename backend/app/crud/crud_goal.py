import uuid
from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.goal import Goal, GoalLink
from app.schemas.goal import GoalCreate, GoalUpdate, GoalLinkCreate, GoalLinkUpdate


class CRUDGoal(CRUDBase[Goal, GoalCreate, GoalUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: GoalCreate, user_id: uuid.UUID
    ) -> Goal:
        db_obj = Goal(**obj_in.model_dump(), user_id=user_id)
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


class CRUDGoalLink(CRUDBase[GoalLink, GoalLinkCreate, GoalLinkUpdate]):
    pass


goal = CRUDGoal(Goal)
goal_link = CRUDGoalLink(GoalLink)
