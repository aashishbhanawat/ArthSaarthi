import uuid
from datetime import date
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
        and portfolios, and computes required monthly SIP.
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
                # calculate its value.
                transactions = (
                    db.query(transaction.Transaction.portfolio_id)
                    .filter(transaction.Transaction.asset_id == link.asset_id)
                    .filter(transaction.Transaction.user_id == goal.user_id)
                    .limit(1)
                    .all()
                )
                if transactions:
                    portfolio_id = transactions[0][0]
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

        # SIP Calculation Engine
        rate_of_return = (
            float(goal.expected_return)
            if goal.expected_return is not None
            else 10.0
        )

        today = date.today()
        days_remaining = (goal.target_date - today).days
        months_remaining = max(0.0, days_remaining / 30.4375)

        target_amt = float(goal.target_amount)
        current_amt = float(current_amount)

        required_sip = 0.0

        if months_remaining > 0:
            if rate_of_return == 0.0:
                required_sip = max(0.0, target_amt - current_amt) / months_remaining
            else:
                monthly_rate = (rate_of_return / 100.0) / 12.0
                future_pv = current_amt * ((1.0 + monthly_rate) ** months_remaining)
                if future_pv < target_amt:
                    remaining_fv = target_amt - future_pv
                    denom = ((1.0 + monthly_rate) ** months_remaining) - 1.0
                    if denom > 0:
                        required_sip = remaining_fv * (monthly_rate / denom)

        return {
            **goal.__dict__,
            "current_amount": current_amount,
            "progress": progress,
            "required_sip": round(required_sip, 2),
            "calculated_return_rate": rate_of_return,
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
