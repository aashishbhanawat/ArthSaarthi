import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import dependencies

router = APIRouter()


@router.get("/", response_model=List[schemas.Goal])
def read_goals(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Retrieve goals for the current user.
    """
    goals = crud.goal.get_multi_by_owner(db=db, user_id=current_user.id)
    return goals


@router.post("/", response_model=schemas.Goal, status_code=201)
def create_goal(
    *,
    db: Session = Depends(dependencies.get_db),
    goal_in: schemas.GoalCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new goal.
    """
    goal = crud.goal.create_with_owner(db=db, obj_in=goal_in, user_id=current_user.id)
    db.commit()
    return goal


@router.get("/{goal_id}", response_model=schemas.Goal)
def read_goal(
    *,
    db: Session = Depends(dependencies.get_db),
    goal_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get goal by ID.
    """
    goal = crud.goal.get(db=db, id=goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return goal


@router.put("/{goal_id}", response_model=schemas.Goal)
def update_goal(
    *,
    db: Session = Depends(dependencies.get_db),
    goal_id: uuid.UUID,
    goal_in: schemas.GoalUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update a goal.
    """
    goal = crud.goal.get(db=db, id=goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    goal = crud.goal.update(db=db, db_obj=goal, obj_in=goal_in)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", response_model=schemas.Msg)
def delete_goal(
    *,
    db: Session = Depends(dependencies.get_db),
    goal_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a goal.
    """
    goal = crud.goal.get(db=db, id=goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    crud.goal.remove(db=db, id=goal_id)
    db.commit()
    return {"msg": "Goal deleted successfully"}
