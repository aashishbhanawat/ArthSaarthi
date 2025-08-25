import random
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.goal import Goal


from decimal import Decimal
from typing import Optional

def create_random_goal(db: Session, *, user_id: uuid.UUID, target_amount: Optional[Decimal] = None) -> Goal:
    """
    Test utility to create a random goal.
    """
    if target_amount is None:
        target_amount = Decimal(str(random.uniform(1000, 50000)))

    goal_in = schemas.GoalCreate(
        name=f"Test Goal {random.randint(1, 1000)}",
        target_amount=target_amount,
        target_date=date(2025, 12, 31),
    )
    return crud.goal.create_with_owner(db=db, obj_in=goal_in, user_id=user_id)
