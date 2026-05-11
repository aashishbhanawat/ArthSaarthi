import uuid
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import transaction
from app.models.goal import Goal, GoalLink
from app.schemas.goal import (
    GoalCreate,
    GoalLinkCreate,
    GoalLinkUpdate,
    GoalUpdate,
)
from app.utils.pydantic_compat import model_dump


class CRUDGoal(CRUDBase[Goal, GoalCreate, GoalUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: GoalCreate, user_id: uuid.UUID
    ) -> Goal:
        db_obj = Goal(**model_dump(obj_in), user_id=user_id)
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

    def get_goal_with_analytics(self, db: Session, *, goal: Goal) -> dict:
        """
        Calculates the current progress of a goal based on its linked assets
        and portfolios.
        """
        current_amount = Decimal("0.0")

        # Optimization: Cache portfolio data to avoid recalculating the same
        # portfolio multiple times if a goal has multiple links to the same
        # portfolio or assets within it.
        portfolio_cache = {}

        from app import crud

        for link in goal.links:
            if link.portfolio_id:
                if link.portfolio_id not in portfolio_cache:
                    portfolio_cache[link.portfolio_id] = (
                        crud.holding.get_portfolio_holdings_and_summary(
                            db, portfolio_id=link.portfolio_id
                        )
                    )
                current_amount += portfolio_cache[link.portfolio_id].summary.total_value
            elif link.asset_id:
                # To get an asset's value, we need to know which portfolio it
                # belongs to. Since a goal can be linked to a standalone asset,
                # we need to find a portfolio that contains this asset to
                # calculate its value. This is a simplification and might not
                # be accurate if the asset is in multiple portfolios. A better
                # approach would be to calculate the value of the asset
                # across all portfolios. For now, we will just find the first
                # portfolio that contains the asset.
                transactions = (
                    db.query(transaction.Transaction)
                    .filter(transaction.Transaction.asset_id == link.asset_id)
                    .filter(transaction.Transaction.user_id == goal.user_id)
                    .all()
                )
                if transactions:
                    portfolio_id = transactions[0].portfolio_id
                    if portfolio_id not in portfolio_cache:
                        portfolio_cache[portfolio_id] = (
                            crud.holding.get_portfolio_holdings_and_summary(
                                db, portfolio_id=portfolio_id
                            )
                        )

                    # Find the asset in the cached holdings
                    for holding in portfolio_cache[portfolio_id].holdings:
                        if holding.asset_id == link.asset_id:
                            current_amount += holding.current_value
                            break

        progress = (
            (current_amount / goal.target_amount) * 100
            if goal.target_amount > 0
            else 0
        )

        return {
            **goal.__dict__,
            "current_amount": current_amount,
            "progress": progress,
        }


class CRUDGoalLink(CRUDBase[GoalLink, GoalLinkCreate, GoalLinkUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: GoalLinkCreate, user_id: uuid.UUID
    ) -> GoalLink:
        db_obj = GoalLink(**model_dump(obj_in), user_id=user_id)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj


goal = CRUDGoal(Goal)
goal_link = CRUDGoalLink(GoalLink)
