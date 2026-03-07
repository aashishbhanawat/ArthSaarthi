from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.schemas.enums import TransactionType


def _calculate_demerger_ratios(
    db: Session,
    portfolio_id: Optional[str],
    end_date: datetime
) -> Dict[str, List[Tuple[datetime, Decimal]]]:
    """
    Returns a dict mapping asset_id (str) to a list of (demerger_date, remaining_ratio)
    where remaining_ratio is the factor by which to multiply the original cost basis.
    """
    # 1. Fetch all DEMERGER transactions before end_date
    query = select(Transaction).where(
        Transaction.transaction_type == TransactionType.DEMERGER,
        Transaction.transaction_date <= end_date
    )
    if portfolio_id:
        query = query.where(Transaction.portfolio_id == portfolio_id)

    demerger_txs = db.scalars(query).all()
    if not demerger_txs:
        return {}

    # Group demergers by asset_id
    # Note: A single asset can have multiple demergers. We will need to sort by date.
    demergers_by_asset: Dict[str, List[Transaction]] = defaultdict(list)
    for tx in demerger_txs:
        if tx.details and "total_cost_allocated" in tx.details:
            demergers_by_asset[str(tx.asset_id)].append(tx)

    if not demergers_by_asset:
        return {}

    # 2. To compute remaining_ratio we need original cost
    # We fetch BUYs before the earliest demerger for each asset

    result: Dict[str, List[Tuple[datetime, Decimal]]] = defaultdict(list)

    for asset_id, d_txs in demergers_by_asset.items():
        # Sort demergers by date
        d_txs.sort(key=lambda x: x.transaction_date)
        earliest_demerger_date = d_txs[0].transaction_date

        # Fetch relevant BUYs for this asset before earliest demerger
        buy_query = select(Transaction).where(
            Transaction.asset_id == asset_id,
            Transaction.transaction_type.in_(["BUY", "ESPP_PURCHASE", "RSU_VEST"]),
            Transaction.transaction_date < earliest_demerger_date
        )
        if portfolio_id:
            buy_query = buy_query.where(Transaction.portfolio_id == portfolio_id)

        buys = db.scalars(buy_query).all()

        pre_demerger_cost = Decimal("0.0")
        for buy in buys:
            price = buy.price_per_unit if buy.price_per_unit else Decimal("0")
            pre_demerger_cost += buy.quantity * price

        current_pre_demerger_cost = pre_demerger_cost

        for d_tx in d_txs:
            cost_allocated = Decimal(str(d_tx.details["total_cost_allocated"]))
            if current_pre_demerger_cost > 0 and cost_allocated > 0:
                remaining_ratio = (
                    current_pre_demerger_cost - cost_allocated
                ) / current_pre_demerger_cost
            else:
                remaining_ratio = Decimal("1.0")

            result[asset_id].append((d_tx.transaction_date, remaining_ratio))

            # For next demerger, the "pre_demerger_cost" is effectively reduced
            # Actually, `total_cost_allocated` in `crud_corporate_action.py`
            # uses the remaining cost basis of the original buys.
            # Let's verify how it behaves with multiple demergers.
            current_pre_demerger_cost -= cost_allocated

    return result
