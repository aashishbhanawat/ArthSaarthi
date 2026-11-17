import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.corporate_action_event import CorporateActionEvent
from app.schemas.corporate_action import CorporateActionEventOut


class CRUDCorporateActionEvent:
    def get_events_by_user(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[CorporateActionEventOut], int, int]:
        """
        Retrieves corporate action events for a user, along with total count
        and count of unread (NEW) events.
        """
        base_query = db.query(CorporateActionEvent).filter(
            CorporateActionEvent.user_id == user_id
        )

        unread_count = (
            db.query(CorporateActionEvent)
            .filter(
                CorporateActionEvent.user_id == user_id,
                CorporateActionEvent.status == "NEW",
            )
            .count()
        )

        if status:
            filtered_query = base_query.filter(CorporateActionEvent.status == status)
        else:
            filtered_query = base_query

        total = filtered_query.count()
        events = (
            filtered_query.order_by(CorporateActionEvent.event_date.desc(), CorporateActionEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Enrich with asset details
        result_items: List[CorporateActionEventOut] = []
        for ev in events:
            asset = db.query(Asset).filter(Asset.id == ev.asset_id).first()
            bond_name = asset.name if asset else None
            isin = asset.bond.isin if (asset and asset.bond) else None

            out = CorporateActionEventOut(
                id=ev.id,
                user_id=ev.user_id,
                portfolio_id=ev.portfolio_id,
                asset_id=ev.asset_id,
                transaction_id=ev.transaction_id,
                event_type=ev.event_type,
                event_date=ev.event_date,
                units=ev.units,
                amount=ev.amount,
                status=ev.status,
                details=ev.details,
                created_at=ev.created_at,
                bond_name=bond_name,
                isin=isin,
            )
            result_items.append(out)

        return result_items, total, unread_count

    def dismiss_event(
        self,
        db: Session,
        *,
        event_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[CorporateActionEvent]:
        """Marks a corporate action event as DISMISSED."""
        event = (
            db.query(CorporateActionEvent)
            .filter(
                CorporateActionEvent.id == event_id,
                CorporateActionEvent.user_id == user_id,
            )
            .first()
        )
        if event:
            event.status = "DISMISSED"
            db.add(event)
            db.commit()
            db.refresh(event)
        return event

    def dismiss_all_by_user(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
    ) -> int:
        """Marks all NEW corporate action events for a user as DISMISSED."""
        updated = (
            db.query(CorporateActionEvent)
            .filter(
                CorporateActionEvent.user_id == user_id,
                CorporateActionEvent.status == "NEW",
            )
            .update({"status": "DISMISSED"}, synchronize_session=False)
        )
        db.commit()
        return updated


crud_corporate_action_event = CRUDCorporateActionEvent()
