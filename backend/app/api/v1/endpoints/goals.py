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


@router.get("/{goal_id}", response_model=schemas.GoalWithAnalytics)
def read_goal(
    *,
    db: Session = Depends(dependencies.get_db),
    goal_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get goal by ID with analytics.
    """
    goal = crud.goal.get(db=db, id=goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    analytics = crud.goal.get_goal_analytics(db=db, goal=goal)
    return {**goal.__dict__, **analytics}


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


@router.post("/{goal_id}/links", response_model=schemas.GoalLink, status_code=201)
def create_goal_link(
    *,
    db: Session = Depends(dependencies.get_db),
    goal_id: uuid.UUID,
    link_in: schemas.GoalLinkCreateIn,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create a new link between a goal and an asset or portfolio.
    """
    goal = crud.goal.get(db=db, id=goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Ensure that either portfolio_id or asset_id is provided, but not both
    if not (link_in.portfolio_id or link_in.asset_id) or \
       (link_in.portfolio_id and link_in.asset_id):
        raise HTTPException(
            status_code=400,
            detail="Either portfolio_id or asset_id must be provided, but not both."
        )

    # Additional checks to ensure the user owns the asset or portfolio can be added here

    goal_link_create = schemas.GoalLinkCreate(
        **link_in.model_dump(), goal_id=goal_id
    )
    link = crud.goal_link.create_with_owner(
        db=db, obj_in=goal_link_create, user_id=current_user.id
    )
    db.commit()
    return link


@router.delete("/{goal_id}/links/{link_id}", response_model=schemas.Msg)
def delete_goal_link(
    *,
    db: Session = Depends(dependencies.get_db),
    goal_id: uuid.UUID,
    link_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a link between a goal and an asset or portfolio.
    """
    goal = crud.goal.get(db=db, id=goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    link = crud.goal_link.get(db=db, id=link_id)
    if not link or link.goal_id != goal_id:
        raise HTTPException(status_code=404, detail="Link not found")

    crud.goal_link.remove(db=db, id=link_id)
    db.commit()
    return {"msg": "Link deleted successfully"}
