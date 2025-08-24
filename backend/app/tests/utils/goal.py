from sqlalchemy.orm import Session
import random
from datetime import date
import uuid

from app import crud, schemas
from app.models.goal import Goal
from app.tests.utils.user import create_random_user


def create_random_goal(db: Session, *, user_id: uuid.UUID) -> Goal:
    """
    Test utility to create a random goal.
    """
    goal_in = schemas.GoalCreate(
        name=f"Test Goal {random.randint(1, 1000)}",
        target_amount=random.uniform(1000, 50000),
        target_date=date(2025, 12, 31),
    )
    return crud.goal.create_with_owner(db=db, obj_in=goal_in, user_id=user_id)
