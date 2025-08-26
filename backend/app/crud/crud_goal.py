import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app import models
from app.crud import crud_analytics, crud_transaction
from app.crud.base import CRUDBase
from app.models.goal import Goal, GoalLink
from app.schemas.goal import GoalCreate, GoalLinkCreate, GoalLinkUpdate, GoalUpdate


def _get_standalone_asset_current_value(
    db: Session, asset_id: uuid.UUID, user_id: uuid.UUID
) -> Decimal:
    """Calculates the current market value of a single asset holding for a user."""
    transactions = crud_transaction.transaction.get_multi_by_asset_and_user(
        db=db, asset_id=asset_id, user_id=user_id
    )
    if not transactions:
        return Decimal("0.0")

    asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
    if not asset:
        return Decimal("0.0")

    net_quantity = Decimal("0.0")
    for t in transactions:
        if t.transaction_type.lower() == "buy":
            net_quantity += t.quantity
        elif t.transaction_type.lower() == "sell":
            net_quantity -= t.quantity

    if net_quantity <= 0:
        return Decimal("0.0")

    asset_to_price = [
        {"ticker_symbol": asset.ticker_symbol, "exchange": asset.exchange}
    ]
    current_prices_details = (
        crud_analytics.financial_data_service.get_current_prices(asset_to_price)
    )

    if asset.ticker_symbol not in current_prices_details:
        return Decimal("0.0")

    price_info = current_prices_details[asset.ticker_symbol]
    current_price = price_info["current_price"]

    return net_quantity * current_price


class CRUDGoal(CRUDBase[Goal, GoalCreate, GoalUpdate]):
    def get(self, db: Session, id: uuid.UUID) -> Optional[Goal]:
        return (
            db.query(self.model)
            .options(
                joinedload(self.model.links).joinedload(GoalLink.portfolio),
                joinedload(self.model.links).joinedload(GoalLink.asset),
            )
            .filter(self.model.id == id)
            .first()
        )

    def get_goal_analytics(self, db: Session, goal: Goal) -> Dict[str, Any]:
        current_value = Decimal("0.0")
        for link in goal.links:
            if link.portfolio_id:
                current_value += crud_analytics._get_portfolio_current_value(
                    db, link.portfolio_id
                )
            elif link.asset_id:
                current_value += _get_standalone_asset_current_value(
                    db, link.asset_id, goal.user_id
                )

        progress = (
            (current_value / goal.target_amount) * 100 if goal.target_amount > 0 else 0
        )

        return {
            "current_value": current_value,
            "progress": progress,
        }

    def create_with_owner(
        self, db: Session, *, obj_in: GoalCreate, user_id: uuid.UUID
    ) -> Goal:
        db_obj = Goal(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.flush()
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
    def create_with_owner(
        self, db: Session, *, obj_in: GoalLinkCreate, user_id: uuid.UUID
    ) -> GoalLink:
        db_obj = GoalLink(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[GoalLink]:
        return (
            db.query(self.model)
            .filter(GoalLink.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


goal = CRUDGoal(Goal)
goal_link = CRUDGoalLink(GoalLink)
