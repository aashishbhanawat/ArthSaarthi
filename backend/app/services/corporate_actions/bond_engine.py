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


def get_candidate_coupon_dates(
    bond: Bond,
    start_date: date,
    end_date: date,
) -> List[date]:
    """
    Returns all valid scheduled coupon payment dates for a bond between
    start_date and end_date (inclusive), respecting payment_frequency,
    first_payment_date, maturity_date, and month-end day calculations.
    """
    if not bond or not bond.coupon_rate or bond.coupon_rate <= 0:
        return []

    effective_start = (
        max(start_date, bond.first_payment_date)
        if bond.first_payment_date
        else start_date
    )
    effective_end = min(end_date, bond.maturity_date)

    if effective_start > effective_end:
        return []

    freq_val = (
        bond.payment_frequency.value
        if hasattr(bond.payment_frequency, "value")
        else str(bond.payment_frequency)
    )
    freq_str = freq_val.upper() if bond.payment_frequency else PaymentFrequency.ANNUALLY.value

    # ON_MATURITY only pays out on maturity date
    if freq_str == PaymentFrequency.ON_MATURITY.value:
        if effective_start <= bond.maturity_date <= effective_end:
            return [bond.maturity_date]
        return []

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

    candidate_dates: List[date] = []
    # Loop over years covering the effective range
    for year in range(effective_start.year - 1, effective_end.year + 1):
        for month in allowed_months:
            last_day = calendar.monthrange(year, month)[1]
            day = min(anchor_day, last_day)
            cand_date = date(year, month, day)
            if effective_start <= cand_date <= effective_end:
                candidate_dates.append(cand_date)

    candidate_dates.sort()
    return candidate_dates


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
    1. Scheduled coupon transactions (DIVIDEND/COUPON) with chronological catch-up/backfill.
    2. Maturity redemption transactions (SELL at face value) when check_date >= maturity_date.
    Guarantees idempotency on duplicate runs and across system downtime.
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
            # Determine earliest transaction date for this bond in this portfolio
            first_tx_date = (
                db.query(func.min(models.Transaction.transaction_date))
                .filter(
                    models.Transaction.portfolio_id == portfolio.id,
                    models.Transaction.asset_id == asset.id,
                )
                .scalar()
            )
            if not first_tx_date:
                continue

            start_date = (
                first_tx_date.date()
                if isinstance(first_tx_date, datetime)
                else first_tx_date
            )
            end_date = min(check_date, bond.maturity_date)

            # Query existing coupon transactions and corporate action events to guarantee idempotency
            existing_txs = (
                db.query(models.Transaction.transaction_date)
                .filter(
                    models.Transaction.portfolio_id == portfolio.id,
                    models.Transaction.asset_id == asset.id,
                    models.Transaction.transaction_type.in_([
                        TransactionType.COUPON.value,
                        TransactionType.DIVIDEND.value,
                    ]),
                )
                .all()
            )
            existing_tx_dates = set(
                tx[0].date() if isinstance(tx[0], datetime) else tx[0]
                for tx in existing_txs
                if tx[0] is not None
            )

            existing_events = (
                db.query(CorporateActionEvent.event_date)
                .filter(
                    CorporateActionEvent.portfolio_id == portfolio.id,
                    CorporateActionEvent.asset_id == asset.id,
                    CorporateActionEvent.event_type == "BOND_COUPON",
                )
                .all()
            )
            existing_event_dates = set(
                ev[0] for ev in existing_events if ev[0] is not None
            )

            # --- 1. Process Scheduled / Missed Coupons (Chronological Catch-Up) ---
            candidate_coupon_dates = get_candidate_coupon_dates(bond, start_date, end_date)
            for coupon_date in candidate_coupon_dates:
                if coupon_date in existing_tx_dates or coupon_date in existing_event_dates:
                    continue

                # Check quantity held on coupon_date
                holding_qty = get_bond_holding_quantity(
                    db, str(portfolio.id), str(asset.id), coupon_date
                )
                if holding_qty <= Decimal("0"):
                    continue

                coupon_amount = calculate_coupon_amount(bond, holding_qty)
                if coupon_amount <= Decimal("0.00"):
                    continue

                coupon_tx = models.Transaction(
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    user_id=portfolio.user_id,
                    transaction_type=TransactionType.COUPON.value,
                    quantity=coupon_amount,
                    price_per_unit=Decimal("1.0"),
                    fees=Decimal("0.0"),
                    transaction_date=datetime.combine(coupon_date, time(0, 0)),
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
                    event_date=coupon_date,
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
                existing_tx_dates.add(coupon_date)
                existing_event_dates.add(coupon_date)
                logger.info(
                    "Created BOND_COUPON payout transaction %s of %s for portfolio %s on date %s",
                    coupon_tx.id,
                    coupon_amount,
                    portfolio.id,
                    coupon_date,
                )

            # --- 2. Check Maturity Redemption (Catch-Up if check_date >= maturity_date) ---
            if check_date >= bond.maturity_date:
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
                existing_maturity_event = (
                    db.query(CorporateActionEvent)
                    .filter(
                        CorporateActionEvent.portfolio_id == portfolio.id,
                        CorporateActionEvent.asset_id == asset.id,
                        CorporateActionEvent.event_type == "BOND_MATURITY",
                    )
                    .first()
                )

                if not existing_redemption and not existing_maturity_event:
                    # Check holding quantity on bond.maturity_date
                    maturity_holding_qty = get_bond_holding_quantity(
                        db, str(portfolio.id), str(asset.id), bond.maturity_date
                    )
                    if maturity_holding_qty > Decimal("0"):
                        face_val = (
                            bond.face_value
                            if (bond.face_value and bond.face_value > 0)
                            else DEFAULT_BOND_FACE_VALUE
                        )
                        redemption_amount = (
                            maturity_holding_qty * face_val
                        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                        # Create SELL transaction
                        sell_tx = models.Transaction(
                            portfolio_id=portfolio.id,
                            asset_id=asset.id,
                            user_id=portfolio.user_id,
                            transaction_type=TransactionType.SELL.value,
                            quantity=maturity_holding_qty,
                            price_per_unit=face_val,
                            fees=Decimal("0.0"),
                            transaction_date=datetime.combine(
                                bond.maturity_date, time(0, 0)
                            ),
                            is_automated=True,
                            details={
                                "action": "BOND_MATURITY",
                                "face_value": float(face_val),
                                "units": float(maturity_holding_qty),
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
                            units=maturity_holding_qty,
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
                            "Created BOND_MATURITY redemption transaction %s for portfolio %s, asset %s on date %s",
                            sell_tx.id,
                            portfolio.id,
                            asset.name,
                            bond.maturity_date,
                        )

    db.commit()
    logger.info("Bond corporate action processing completed. Total events created: %d", len(created_events))
    return created_events
