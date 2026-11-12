import calendar
import logging
from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional, Union

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.models.bond import Bond
from app.models.corporate_action_event import CorporateActionEvent
from app.schemas.asset import AssetType
from app.schemas.enums import PaymentFrequency, TransactionType

logger = logging.getLogger(__name__)

DEFAULT_BOND_FACE_VALUE = Decimal("1000.00")


def get_frequency_divisor(frequency: Optional[Union[str, PaymentFrequency]]) -> int:
    """Returns the annual frequency divisor for a given PaymentFrequency."""
    if not frequency:
        return 1
    val = frequency.value if hasattr(frequency, "value") else str(frequency)
    freq_str = val.upper()
    if freq_str == PaymentFrequency.ANNUALLY.value:
        return 1
    elif freq_str == PaymentFrequency.SEMI_ANNUALLY.value:
        return 2
    elif freq_str == PaymentFrequency.QUARTERLY.value:
        return 4
    elif freq_str == PaymentFrequency.MONTHLY.value:
        return 12
    elif freq_str == PaymentFrequency.ON_MATURITY.value:
        return 1
    return 1


def is_coupon_due(bond: Bond, check_date: date) -> bool:
    """
    Determines if a periodic coupon payout is due for the given bond on check_date.
    Uses first_payment_date (if present) or maturity_date as the anchor.
    """
    if not bond or not bond.coupon_rate or bond.coupon_rate <= 0:
        return False

    if check_date > bond.maturity_date:
        return False

    if bond.first_payment_date and check_date < bond.first_payment_date:
        return False

    freq_val = (
        bond.payment_frequency.value
        if hasattr(bond.payment_frequency, "value")
        else str(bond.payment_frequency)
    )
    freq_str = freq_val.upper() if bond.payment_frequency else PaymentFrequency.ANNUALLY.value

    # ON_MATURITY only pays out exactly on the maturity date
    if freq_str == PaymentFrequency.ON_MATURITY.value:
        return check_date == bond.maturity_date

    anchor_date = bond.first_payment_date or bond.maturity_date
    anchor_day = anchor_date.day
    anchor_month = anchor_date.month

    if freq_str == PaymentFrequency.ANNUALLY.value:
        allowed_months = [anchor_month]
    elif freq_str == PaymentFrequency.SEMI_ANNUALLY.value:
        allowed_months = [anchor_month, (anchor_month + 6 - 1) % 12 + 1]
    elif freq_str == PaymentFrequency.QUARTERLY.value:
        allowed_months = [(anchor_month + 3 * i - 1) % 12 + 1 for i in range(4)]
    elif freq_str == PaymentFrequency.MONTHLY.value:
        allowed_months = list(range(1, 13))
    else:
        allowed_months = [anchor_month]

    if check_date.month not in allowed_months:
        return False

    last_day_of_month = calendar.monthrange(check_date.year, check_date.month)[1]
    target_day = min(anchor_day, last_day_of_month)

    return check_date.day == target_day


def calculate_coupon_amount(bond: Bond, quantity: Decimal) -> Decimal:
    """
    Calculates coupon payout amount for the given quantity of bond units.
    Coupon Payout = (Face Value * (Coupon Rate / 100) / Frequency Divisor) * Quantity
    """
    if not bond or not bond.coupon_rate or quantity <= 0:
        return Decimal("0.00")

    face_val = bond.face_value if (bond.face_value and bond.face_value > 0) else DEFAULT_BOND_FACE_VALUE
    coupon_pct = Decimal(str(bond.coupon_rate)) / Decimal("100")
    annual_coupon_per_unit = face_val * coupon_pct

    divisor = Decimal(str(get_frequency_divisor(bond.payment_frequency)))
    coupon_per_unit = annual_coupon_per_unit / divisor

    total_amount = coupon_per_unit * Decimal(str(quantity))
    return total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_bond_holding_quantity(
    db: Session,
    portfolio_id: str,
    asset_id: str,
    as_of_date: date,
) -> Decimal:
    """
    Calculates active bond units held in a portfolio as of a specific date.
    Holding = sum(BUY/VEST quantities) - sum(SELL quantities).
    """
    cutoff_datetime = datetime.combine(as_of_date, time(23, 59, 59))

    txs = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio_id,
            models.Transaction.asset_id == asset_id,
            models.Transaction.transaction_date <= cutoff_datetime,
        )
        .all()
    )

    total_qty = Decimal("0.00000000")
    for tx in txs:
        tx_type = tx.transaction_type.upper()
        if tx_type in ("BUY", "ESPP_PURCHASE", "RSU_VEST"):
            total_qty += Decimal(str(tx.quantity))
        elif tx_type == "SELL":
            total_qty -= Decimal(str(tx.quantity))

    return total_qty


def process_bond_corporate_actions(
    db: Session,
    check_date: Optional[date] = None,
) -> List[CorporateActionEvent]:
    """
    Core engine that scans all portfolios with bond holdings and generates:
    1. Scheduled coupon transactions (DIVIDEND/COUPON)
    2. Maturity redemption transactions (SELL at face value)
    Guarantees idempotency on duplicate runs.
    """
    if check_date is None:
        check_date = date.today()

    logger.info("Starting bond corporate action processing for date: %s", check_date)

    # Find all Bond assets
    bond_assets = (
        db.query(models.Asset)
        .join(Bond, models.Asset.id == Bond.asset_id)
        .filter(models.Asset.asset_type == AssetType.BOND)
        .all()
    )

    if not bond_assets:
        logger.info("No bond assets found in master database.")
        return []

    created_events: List[CorporateActionEvent] = []

    for asset in bond_assets:
        bond: Bond = asset.bond
        if not bond:
            continue

        # Find portfolios holding this asset
        portfolios_with_bond = (
            db.query(models.Portfolio)
            .join(models.Transaction, models.Portfolio.id == models.Transaction.portfolio_id)
            .filter(models.Transaction.asset_id == asset.id)
            .distinct()
            .all()
        )

        for portfolio in portfolios_with_bond:
            holding_qty = get_bond_holding_quantity(db, str(portfolio.id), str(asset.id), check_date)
            if holding_qty <= Decimal("0"):
                continue

            # --- 1. Check Maturity Redemption ---
            if check_date >= bond.maturity_date:
                # Check if already redeemed
                existing_redemption = (
                    db.query(models.Transaction)
                    .filter(
                        models.Transaction.portfolio_id == portfolio.id,
                        models.Transaction.asset_id == asset.id,
                        models.Transaction.transaction_type == TransactionType.SELL.value,
                        models.Transaction.is_automated.is_(True),
                    )
                    .first()
                )

                if not existing_redemption:
                    face_val = bond.face_value if (bond.face_value and bond.face_value > 0) else DEFAULT_BOND_FACE_VALUE
                    redemption_amount = (holding_qty * face_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                    # Create SELL transaction
                    sell_tx = models.Transaction(
                        portfolio_id=portfolio.id,
                        asset_id=asset.id,
                        user_id=portfolio.user_id,
                        transaction_type=TransactionType.SELL.value,
                        quantity=holding_qty,
                        price_per_unit=face_val,
                        fees=Decimal("0.0"),
                        transaction_date=datetime.combine(bond.maturity_date, time(0, 0)),
                        is_automated=True,
                        details={
                            "action": "BOND_MATURITY",
                            "face_value": float(face_val),
                            "units": float(holding_qty),
                        },
                    )
                    db.add(sell_tx)
                    db.flush()

                    # Record event
                    event = CorporateActionEvent(
                        user_id=portfolio.user_id,
                        portfolio_id=portfolio.id,
                        asset_id=asset.id,
                        transaction_id=sell_tx.id,
                        event_type="BOND_MATURITY",
                        event_date=bond.maturity_date,
                        units=holding_qty,
                        amount=redemption_amount,
                        status="NEW",
                        details={
                            "bond_name": asset.name,
                            "isin": bond.isin,
                            "face_value": float(face_val),
                        },
                    )
                    db.add(event)
                    db.flush()
                    created_events.append(event)
                    logger.info(
                        "Created BOND_MATURITY redemption transaction %s for portfolio %s, asset %s",
                        sell_tx.id,
                        portfolio.id,
                        asset.name,
                    )

            # --- 2. Check Coupon Payout ---
            if is_coupon_due(bond, check_date):
                # Check idempotency: no existing COUPON on check_date
                existing_coupon = (
                    db.query(models.Transaction)
                    .filter(
                        models.Transaction.portfolio_id == portfolio.id,
                        models.Transaction.asset_id == asset.id,
                        models.Transaction.transaction_type == TransactionType.COUPON.value,
                        func.date(models.Transaction.transaction_date) == check_date,
                    )
                    .first()
                )

                if not existing_coupon:
                    coupon_amount = calculate_coupon_amount(bond, holding_qty)
                    if coupon_amount > Decimal("0.00"):
                        coupon_tx = models.Transaction(
                            portfolio_id=portfolio.id,
                            asset_id=asset.id,
                            user_id=portfolio.user_id,
                            transaction_type=TransactionType.COUPON.value,
                            quantity=coupon_amount,
                            price_per_unit=Decimal("1.0"),
                            fees=Decimal("0.0"),
                            transaction_date=datetime.combine(check_date, time(0, 0)),
                            is_automated=True,
                            details={
                                "action": "BOND_COUPON",
                                "coupon_rate": float(bond.coupon_rate or 0),
                                "payment_frequency": str(bond.payment_frequency),
                                "units": float(holding_qty),
                            },
                        )
                        db.add(coupon_tx)
                        db.flush()

                        event = CorporateActionEvent(
                            user_id=portfolio.user_id,
                            portfolio_id=portfolio.id,
                            asset_id=asset.id,
                            transaction_id=coupon_tx.id,
                            event_type="BOND_COUPON",
                            event_date=check_date,
                            units=holding_qty,
                            amount=coupon_amount,
                            status="NEW",
                            details={
                                "bond_name": asset.name,
                                "isin": bond.isin,
                                "coupon_rate": float(bond.coupon_rate or 0),
                                "payment_frequency": str(bond.payment_frequency),
                            },
                        )
                        db.add(event)
                        db.flush()
                        created_events.append(event)
                        logger.info(
                            "Created BOND_COUPON payout transaction %s of %s for portfolio %s",
                            coupon_tx.id,
                            coupon_amount,
                            portfolio.id,
                        )

    db.commit()
    logger.info("Bond corporate action processing completed. Total events created: %d", len(created_events))
    return created_events
