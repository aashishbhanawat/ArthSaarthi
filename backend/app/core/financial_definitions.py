import logging
from enum import Enum
from typing import Any, Dict

from app.schemas.enums import TransactionType

logger = logging.getLogger(__name__)


class CashFlowType(Enum):
    """Defines the direction of cash movement for a transaction."""
    INFLOW = 1
    OUTFLOW = -1
    NONE = 0


class PnlImpactType(Enum):
    """Defines how a transaction impacts realized profit and loss."""
    INCOME = "INCOME"
    FROM_SALE = "FROM_SALE"
    NONE = "NONE"


class QuantityImpact(Enum):
    """Defines how a transaction impacts the quantity of an asset held."""
    ADD = 1
    SUBTRACT = -1
    NONE = 0


TRANSACTION_BEHAVIORS: Dict[TransactionType, Dict[str, Any]] = {
    # --- Outflows ---
    TransactionType.BUY: {
        "cash_flow": CashFlowType.OUTFLOW,
        "pnl_impact": PnlImpactType.NONE,
        "quantity_impact": QuantityImpact.ADD,
    },
    TransactionType.CONTRIBUTION: {
        "cash_flow": CashFlowType.OUTFLOW,
        "pnl_impact": PnlImpactType.NONE,
        "quantity_impact": QuantityImpact.ADD,
    },
    # ESPP/RSU acquisitions are treated as outflows (cost basis or taxed amount)
    TransactionType.ESPP_PURCHASE: {
        "cash_flow": CashFlowType.OUTFLOW,
        "pnl_impact": PnlImpactType.NONE,
        "quantity_impact": QuantityImpact.ADD,
    },
    TransactionType.RSU_VEST: {
        "cash_flow": CashFlowType.OUTFLOW,
        "pnl_impact": PnlImpactType.NONE,
        "quantity_impact": QuantityImpact.ADD,
    },

    # --- Inflows ---
    TransactionType.SELL: {
        "cash_flow": CashFlowType.INFLOW,
        "pnl_impact": PnlImpactType.FROM_SALE,
        "quantity_impact": QuantityImpact.SUBTRACT,
    },
    TransactionType.DIVIDEND: {
        "cash_flow": CashFlowType.INFLOW,
        "pnl_impact": PnlImpactType.INCOME,
        "quantity_impact": QuantityImpact.NONE,
    },
    TransactionType.COUPON: {
        "cash_flow": CashFlowType.INFLOW,
        "pnl_impact": PnlImpactType.INCOME,
        "quantity_impact": QuantityImpact.NONE,
    },
    TransactionType.INTEREST_CREDIT: {
        "cash_flow": CashFlowType.INFLOW,
        "pnl_impact": PnlImpactType.INCOME,
        "quantity_impact": QuantityImpact.NONE,
    },
    # --- Non-Cash-Flow Events ---
    TransactionType.SPLIT: {
        "cash_flow": CashFlowType.NONE,
        "pnl_impact": PnlImpactType.NONE,
        "quantity_impact": QuantityImpact.NONE,
    },
    TransactionType.BONUS: {
        "cash_flow": CashFlowType.NONE,
        "pnl_impact": PnlImpactType.NONE,
        "quantity_impact": QuantityImpact.ADD,
    },
}
