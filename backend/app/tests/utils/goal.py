import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Goal
from app.schemas import GoalCreate


def create_random_goal(db: Session, user_id: str) -> Goal:
    name = f"Test Goal {random.randint(1, 1000)}"
    target_amount = random.uniform(1000, 50000)
    target_date = date.today() + timedelta(days=random.randint(30, 365))
    goal_in = GoalCreate(
        name=name,
        target_amount=target_amount,
        target_date=target_date,
    )
    goal = Goal(**goal_in.model_dump(), user_id=user_id)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal
