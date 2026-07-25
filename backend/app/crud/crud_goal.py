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
        and portfolios, computes combined XIRR, projected future value,
        status, and required monthly SIP.
        """
        import math

        from dateutil.relativedelta import relativedelta

        from app import crud
        from app.crud.crud_analytics import _calculate_xirr, _get_portfolio_cash_flows
        from app.models.transaction import Transaction

        current_amount = Decimal("0.0")

        # Optimization: Cache portfolio data to avoid recalculating the same
        # portfolio multiple times if a goal has multiple links to the same
        # portfolio or assets within it.
        portfolio_cache = {}

        # Compile cash flows for XIRR calculation
        all_cash_flows = []
        portfolio_ids_processed = set()
        asset_ids_processed = set()

        for link in goal.links:
            if link.portfolio_id:
                if link.portfolio_id not in portfolio_cache:
                    portfolio_cache[link.portfolio_id] = (
                        crud.holding.get_portfolio_holdings_and_summary(
                            db, portfolio_id=link.portfolio_id
                        )
                    )
                current_amount += portfolio_cache[link.portfolio_id].summary.total_value

                if link.portfolio_id not in portfolio_ids_processed:
                    portfolio_ids_processed.add(link.portfolio_id)
                    transactions = crud.transaction.get_multi_by_portfolio(
                        db, portfolio_id=link.portfolio_id
                    )
                    all_fixed_deposits = crud.fixed_deposit.get_multi_by_portfolio(
                        db, portfolio_id=link.portfolio_id
                    )
                    all_recurring_deposits = (
                        crud.recurring_deposit.get_multi_by_portfolio(
                            db, portfolio_id=link.portfolio_id
                        )
                    )
                    cfs = _get_portfolio_cash_flows(
                        transactions, all_fixed_deposits, all_recurring_deposits
                    )
                    all_cash_flows.extend(cfs)

            elif link.asset_id:
                # To get an asset's value, we need to know which portfolio it
                # belongs to. Since a goal can be linked to a standalone asset,
                # we need to find a portfolio that contains this asset to
                # calculate its value.
                transactions = (
                    db.query(transaction.Transaction.portfolio_id)
                    .filter(transaction.Transaction.asset_id == link.asset_id)
                    .filter(transaction.Transaction.user_id == goal.user_id)
                    .all()
                )
                if transactions:
                    # Find all unique portfolio IDs containing this asset for this user
                    portfolio_ids = list(
                        set(tx.portfolio_id for tx in transactions if tx.portfolio_id)
                    )
                    for portfolio_id in portfolio_ids:
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

                if link.asset_id not in asset_ids_processed:
                    asset_ids_processed.add(link.asset_id)
                    user_transactions = (
                        db.query(Transaction)
                        .filter(Transaction.asset_id == link.asset_id)
                        .filter(Transaction.user_id == goal.user_id)
                        .all()
                    )
                    if user_transactions:
                        cfs = _get_portfolio_cash_flows(user_transactions, [], [])
                        all_cash_flows.extend(cfs)

        progress = (
            (current_amount / goal.target_amount) * 100
            if goal.target_amount > 0
            else 0
        )

        # Calculate combined XIRR
        combined_xirr = 0.0
        if current_amount > 0 and all_cash_flows:
            xirr_flows = list(all_cash_flows)
            xirr_flows.append((date.today(), current_amount))
            xirr_flows = sorted(xirr_flows, key=lambda x: x[0])
            dates, values = zip(*xirr_flows)
            try:
                xirr_rate = _calculate_xirr(list(dates), list(values))
                combined_xirr = xirr_rate * 100.0
            except Exception:
                combined_xirr = 0.0

        if math.isnan(combined_xirr) or math.isinf(combined_xirr):
            combined_xirr = 0.0

        is_xirr_valid = (
            combined_xirr > 0.0
            and combined_xirr <= 100.0
            and not math.isnan(combined_xirr)
            and not math.isinf(combined_xirr)
        )

        rate_of_return = (
            combined_xirr
            if is_xirr_valid
            else (
                float(goal.expected_return)
                if goal.expected_return is not None
                else 10.0
            )
        )

        today = date.today()
        days_remaining = (goal.target_date - today).days
        months_remaining = max(0.0, days_remaining / 30.4375)

        target_amt = float(goal.target_amount)
        current_amt = float(current_amount)

        # Future Value projection of current investments
        projected_future_value = current_amt
        if months_remaining > 0 and rate_of_return > 0:
            monthly_rate = (rate_of_return / 100.0) / 12.0
            projected_future_value = current_amt * (
                (1.0 + monthly_rate) ** months_remaining
            )

        # Status determination
        status = "On Track" if projected_future_value >= target_amt else "Off Track"

        # SIP Calculation Engine
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

        # Generate projection chart data
        projection_chart_data = []
        if months_remaining > 0:
            if months_remaining <= 24:
                step_months = 1
            elif months_remaining <= 120:
                step_months = 3
            else:
                step_months = 12

            # Start point (Today)
            projection_chart_data.append({
                "date": today.strftime("%Y-%m-%d"),
                "projected_value": round(current_amt, 2),
                "target_value": round(current_amt, 2),
            })

            m = step_months
            monthly_rate = (rate_of_return / 100.0) / 12.0
            while m < months_remaining:
                point_date = today + relativedelta(months=int(m))
                proj_val = current_amt * ((1.0 + monthly_rate) ** m)

                if monthly_rate == 0:
                    tgt_val = current_amt + (required_sip * m)
                else:
                    tgt_val = current_amt * ((1.0 + monthly_rate) ** m) + (
                        required_sip
                        * (((1.0 + monthly_rate) ** m - 1.0) / monthly_rate)
                    )

                projection_chart_data.append({
                    "date": point_date.strftime("%Y-%m-%d"),
                    "projected_value": round(proj_val, 2),
                    "target_value": round(tgt_val, 2),
                })
                m += step_months

            # Final target point
            projection_chart_data.append({
                "date": goal.target_date.strftime("%Y-%m-%d"),
                "projected_value": round(projected_future_value, 2),
                "target_value": round(target_amt, 2),
            })
        else:
            # target date is today or in the past
            projection_chart_data.append({
                "date": today.strftime("%Y-%m-%d"),
                "projected_value": round(current_amt, 2),
                "target_value": round(target_amt, 2),
            })

        return {
            **goal.__dict__,
            "current_amount": current_amount,
            "progress": progress,
            "required_sip": round(required_sip, 2),
            "calculated_return_rate": rate_of_return,
            "linked_assets_xirr": round(combined_xirr, 2),
            "projected_future_value": round(projected_future_value, 2),
            "status": status,
            "projection_chart_data": projection_chart_data,
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
