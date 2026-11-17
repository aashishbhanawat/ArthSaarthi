import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.crud.crud_corporate_action_event import crud_corporate_action_event
from app.db.session import get_db
from app.schemas.corporate_action import (
    CorporateActionEventListResponse,
    CorporateActionEventOut,
    CorporateActionTriggerResponse,
)
from app.services.corporate_actions.bond_engine import process_bond_corporate_actions

router = APIRouter()


@router.get(
    "/events",
    response_model=CorporateActionEventListResponse,
    summary="List user corporate action receipts",
)
def get_user_corporate_action_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> CorporateActionEventListResponse:
    """Returns corporate action receipts and unread count for the current user."""
    items, total, unread_count = crud_corporate_action_event.get_events_by_user(
        db,
        user_id=current_user.id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return CorporateActionEventListResponse(
        items=items, total=total, unread_count=unread_count
    )


@router.post(
    "/events/{event_id}/dismiss",
    response_model=CorporateActionEventOut,
    summary="Dismiss a corporate action receipt",
)
def dismiss_corporate_action_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> CorporateActionEventOut:
    """Marks a single corporate action event as DISMISSED."""
    event = crud_corporate_action_event.dismiss_event(
        db, event_id=event_id, user_id=current_user.id
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate action event not found",
        )
    return CorporateActionEventOut.model_validate(event)


@router.post(
    "/events/dismiss-all",
    summary="Dismiss all unread corporate action receipts",
)
def dismiss_all_corporate_action_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> dict:
    """Marks all NEW corporate action receipts for the current user as DISMISSED."""
    dismissed_count = crud_corporate_action_event.dismiss_all_by_user(
        db, user_id=current_user.id
    )
    return {
        "message": f"Successfully dismissed {dismissed_count} corporate action event(s).",
        "dismissed_count": dismissed_count,
    }


@router.post(
    "/admin/process-bonds",
    response_model=CorporateActionTriggerResponse,
    summary="Admin trigger for bond corporate action processing",
)
def admin_process_bond_corporate_actions(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> CorporateActionTriggerResponse:
    """Manually triggers evaluation of bond coupon payouts and maturity redemptions."""
    events = process_bond_corporate_actions(db)
    return CorporateActionTriggerResponse(
        message=f"Bond corporate action processing completed. {len(events)} event(s) generated.",
        events_created=len(events),
        status="SUCCESS",
    )
