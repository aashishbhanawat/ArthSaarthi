import logging
import math
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.models.corporate_action_event import CorporateActionEvent
from app.schemas.asset import AssetType
from app.schemas.enums import TransactionType
from app.schemas.stock_corporate_action import RawStockCorporateAction
from app.services.corporate_actions.exchange_provider import (
    fetch_bse_corporate_actions,
    fetch_nse_corporate_actions,
    fetch_yfinance_corporate_actions,
)

logger = logging.getLogger(__name__)


def get_stock_holding_quantity(
    db: Session,
    portfolio_id: UUID | str,
    asset_id: UUID | str,
    as_of_date: date,
) -> Decimal:
    """
    Calculates active shares held in a portfolio as of a specific date.
    Holding = sum(BUY/VEST/BONUS quantities) - sum(SELL quantities), adjusted for SPLITs.
    """
    cutoff_datetime = datetime.combine(as_of_date, time(23, 59, 59))

    txs = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.portfolio_id == portfolio_id,
            models.Transaction.asset_id == asset_id,
            models.Transaction.transaction_date <= cutoff_datetime,
        )
        .order_by(models.Transaction.transaction_date.asc(), models.Transaction.id.asc())
        .all()
    )

    asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()

    total_qty = Decimal("0.00000000")
    for tx in txs:
        tx_type = tx.transaction_type.upper()
        if tx_type in ("BUY", "ESPP_PURCHASE", "RSU_VEST"):
            total_qty += Decimal(str(tx.quantity))
        elif tx_type == "SELL":
            total_qty -= Decimal(str(tx.quantity))
        elif tx_type == "SPLIT":
            # Split multiplier: ratio = new_ratio / old_ratio
            # quantity = new, price_per_unit = old
            if tx.price_per_unit and tx.price_per_unit > 0:
                multiplier = Decimal(str(tx.quantity)) / Decimal(str(tx.price_per_unit))
                total_qty = total_qty * multiplier
                if asset and asset.currency == "INR":
                    total_qty = Decimal(math.floor(total_qty))
        elif tx_type in ("MERGER", "RENAME"):
            total_qty = Decimal("0.0")

    return total_qty


def get_active_stock_assets(db: Session) -> List[models.Asset]:
    """
    Returns unique stock/ETF assets that are currently held in any user portfolio.
    """
    return (
        db.query(models.Asset)
        .join(models.Transaction, models.Asset.id == models.Transaction.asset_id)
        .filter(models.Asset.asset_type.in_([AssetType.STOCK, AssetType.ETF]))
        .distinct()
        .all()
    )


def fetch_all_stock_corporate_actions(
    target_symbols: Optional[Set[str]] = None,
    symbol_exchange_map: Optional[Dict[str, Optional[str]]] = None,
) -> List[RawStockCorporateAction]:
    """
    Fetches corporate actions from NSE, BSE, and yfinance (fallback / global).
    Deduplicates actions by (symbol, action_type, ex_date).
    """
    actions_by_key: Dict[Tuple[str, str, date], RawStockCorporateAction] = {}

    # 1. Fetch from NSE
    try:
        nse_actions = fetch_nse_corporate_actions()
        for action in nse_actions:
            key = (action.symbol.upper(), action.action_type.upper(), action.ex_date)
            actions_by_key[key] = action
    except Exception as e:
        logger.warning("Error fetching NSE corporate actions: %s", e)

    # 2. Fetch from BSE
    try:
        bse_actions = fetch_bse_corporate_actions()
        for action in bse_actions:
            key = (action.symbol.upper(), action.action_type.upper(), action.ex_date)
            if key not in actions_by_key:
                actions_by_key[key] = action
    except Exception as e:
        logger.warning("Error fetching BSE corporate actions: %s", e)

    # 3. If target_symbols provided, check any target symbol missing from NSE/BSE or non-INR
    if target_symbols and symbol_exchange_map:
        for symbol in target_symbols:
            sym_upper = symbol.upper()
            # If no actions found from NSE/BSE, query yfinance
            has_action = any(k[0] == sym_upper for k in actions_by_key)
            exchange = symbol_exchange_map.get(sym_upper)
            if not has_action or str(exchange).upper() not in ("NSE", "BSE", "NSI"):
                try:
                    yf_actions = fetch_yfinance_corporate_actions(sym_upper, exchange)
                    for action in yf_actions:
                        key = (action.symbol.upper(), action.action_type.upper(), action.ex_date)
                        if key not in actions_by_key:
                            actions_by_key[key] = action
                except Exception as e:
                    logger.warning("Error fetching yfinance fallback for %s: %s", sym_upper, e)

    return list(actions_by_key.values())


def process_stock_corporate_actions(
    db: Session,
    check_date: Optional[date] = None,
    custom_actions: Optional[List[RawStockCorporateAction]] = None,
    max_lookback_days: Optional[int] = 30,
) -> List[CorporateActionEvent]:
    """
    Core engine that scans all portfolios with stock holdings, discovers applicable
    corporate actions (Dividends, Splits, Bonus issues), and executes them.
    Guarantees idempotency on duplicate runs.
    Restricted to max_lookback_days (default 30 days) to prevent retroactively replaying
    historical corporate actions over user portfolios whose imported tradebooks already
    incorporate past bonus shares, splits, or dividends.
    """
    if check_date is None:
        check_date = date.today()

    logger.info("Starting stock corporate action processing for check_date: %s", check_date)

    # 1. Fetch all stock/ETF assets currently held in portfolios
    stock_assets = get_active_stock_assets(db)
    if not stock_assets:
        logger.info("No active stock assets found across portfolios.")
        return []

    asset_map: Dict[str, models.Asset] = {a.ticker_symbol.upper(): a for a in stock_assets}
    symbol_exchange_map: Dict[str, Optional[str]] = {
        a.ticker_symbol.upper(): a.exchange for a in stock_assets
    }

    # 2. Fetch corporate actions (or use injected custom_actions for testing)
    actions = (
        custom_actions
        if custom_actions is not None
        else fetch_all_stock_corporate_actions(
            target_symbols=set(asset_map.keys()),
            symbol_exchange_map=symbol_exchange_map,
        )
    )

    created_events: List[CorporateActionEvent] = []

    for action in actions:
        sym = action.symbol.upper()
        if sym not in asset_map:
            continue

        asset = asset_map[sym]
        if action.ex_date > check_date:
            # Action is scheduled for the future; skip until ex_date arrives
            continue

        if max_lookback_days is not None and action.ex_date < check_date - timedelta(days=max_lookback_days):
            logger.debug(
                "Skipping historical %s for %s: ex_date %s is older than lookback %s days",
                action.action_type,
                sym,
                action.ex_date,
                max_lookback_days,
            )
            continue

        # Find portfolios holding this asset
        portfolios = (
            db.query(models.Portfolio)
            .join(models.Transaction, models.Portfolio.id == models.Transaction.portfolio_id)
            .filter(models.Transaction.asset_id == asset.id)
            .distinct()
            .all()
        )

        for portfolio in portfolios:
            holding_qty = get_stock_holding_quantity(db, portfolio.id, asset.id, action.ex_date)
            if holding_qty <= Decimal("0"):
                continue

            # Query existing corporate action event for idempotency
            existing_event = (
                db.query(CorporateActionEvent)
                .filter(
                    CorporateActionEvent.portfolio_id == portfolio.id,
                    CorporateActionEvent.asset_id == asset.id,
                    CorporateActionEvent.event_type == action.action_type.upper(),
                    CorporateActionEvent.event_date >= action.ex_date - timedelta(days=7),
                    CorporateActionEvent.event_date <= action.ex_date + timedelta(days=7),
                )
                .first()
            )
            if existing_event:
                continue

            # For SPLIT and BONUS: check if an existing transaction already reflects this corporate action
            # (e.g., an imported broker tradebook often records bonus shares as BUY with price_per_unit = 0,
            # or records SPLIT/BONUS near the ex_date/credit date)
            if action.action_type.upper() in ("SPLIT", "BONUS"):
                window_start = action.ex_date - timedelta(days=15)
                window_end = action.ex_date + timedelta(days=15)
                existing_matching_tx = (
                    db.query(models.Transaction)
                    .filter(
                        models.Transaction.portfolio_id == portfolio.id,
                        models.Transaction.asset_id == asset.id,
                        func.date(models.Transaction.transaction_date) >= window_start,
                        func.date(models.Transaction.transaction_date) <= window_end,
                        or_(
                            models.Transaction.transaction_type.in_(["SPLIT", "BONUS"]),
                            and_(
                                models.Transaction.transaction_type == "BUY",
                                models.Transaction.price_per_unit <= Decimal("0.0001"),
                            ),
                        ),
                    )
                    .first()
                )
                if existing_matching_tx:
                    logger.info(
                        "Skipping automated %s for %s on %s: existing corporate action or zero-cost BUY found (%s)",
                        action.action_type,
                        sym,
                        action.ex_date,
                        existing_matching_tx.id,
                    )
                    continue

            # For DIVIDEND: check if an existing dividend transaction exists within a small window
            if action.action_type.upper() == "DIVIDEND":
                window_start = action.ex_date - timedelta(days=3)
                window_end = action.ex_date + timedelta(days=3)
                existing_div = (
                    db.query(models.Transaction)
                    .filter(
                        models.Transaction.portfolio_id == portfolio.id,
                        models.Transaction.asset_id == asset.id,
                        models.Transaction.transaction_type == "DIVIDEND",
                        func.date(models.Transaction.transaction_date) >= window_start,
                        func.date(models.Transaction.transaction_date) <= window_end,
                    )
                    .first()
                )
                if existing_div:
                    logger.info(
                        "Skipping automated DIVIDEND for %s on %s: existing dividend transaction found (%s)",
                        sym,
                        action.ex_date,
                        existing_div.id,
                    )
                    continue

            # --- Process DIVIDEND ---
            if action.action_type.upper() == "DIVIDEND":
                div_per_share = action.dividend_amount or Decimal("0.00")
                if div_per_share <= Decimal("0.00"):
                    continue

                total_dividend = (holding_qty * div_per_share).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

                div_tx = models.Transaction(
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    user_id=portfolio.user_id,
                    transaction_type=TransactionType.DIVIDEND.value,
                    quantity=total_dividend,
                    price_per_unit=Decimal("1.0"),
                    fees=Decimal("0.0"),
                    transaction_date=datetime.combine(action.ex_date, time(0, 0)),
                    is_automated=True,
                    details={
                        "action": "STOCK_DIVIDEND",
                        "dividend_per_share": float(div_per_share),
                        "units": float(holding_qty),
                        "source": action.source,
                    },
                )
                db.add(div_tx)
                db.flush()

                event = CorporateActionEvent(
                    user_id=portfolio.user_id,
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    transaction_id=div_tx.id,
                    event_type="DIVIDEND",
                    event_date=action.ex_date,
                    units=holding_qty,
                    amount=total_dividend,
                    status="NEW",
                    details={
                        "stock_name": asset.name,
                        "symbol": asset.ticker_symbol,
                        "dividend_per_share": float(div_per_share),
                        "source": action.source,
                    },
                )
                db.add(event)
                db.flush()
                created_events.append(event)
                logger.info(
                    "Created automated DIVIDEND transaction %s for portfolio %s on date %s",
                    div_tx.id,
                    portfolio.id,
                    action.ex_date,
                )

            # --- Process STOCK SPLIT ---
            elif action.action_type.upper() == "SPLIT":
                num = action.ratio_numerator or Decimal("1")
                den = action.ratio_denominator or Decimal("1")
                if num <= Decimal("0") or den <= Decimal("0"):
                    continue

                split_tx_in = schemas.TransactionCreate(
                    asset_id=asset.id,
                    portfolio_id=portfolio.id,
                    transaction_type=TransactionType.SPLIT,
                    quantity=num,
                    price_per_unit=den,
                    fees=Decimal("0.0"),
                    transaction_date=datetime.combine(action.ex_date, time(0, 0)),
                    details={
                        "action": "STOCK_SPLIT",
                        "split_ratio": f"{num}:{den}",
                        "source": action.source,
                        "is_automated": True,
                    },
                )
                split_tx = crud.crud_corporate_action.handle_stock_split(
                    db=db,
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    transaction_in=split_tx_in,
                )
                split_tx.is_automated = True
                db.add(split_tx)
                db.flush()

                event = CorporateActionEvent(
                    user_id=portfolio.user_id,
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    transaction_id=split_tx.id,
                    event_type="SPLIT",
                    event_date=action.ex_date,
                    units=holding_qty,
                    amount=Decimal("0.00"),
                    status="NEW",
                    details={
                        "stock_name": asset.name,
                        "symbol": asset.ticker_symbol,
                        "split_ratio": f"{num}:{den}",
                        "source": action.source,
                    },
                )
                db.add(event)
                db.flush()
                created_events.append(event)
                logger.info(
                    "Created automated SPLIT transaction %s for portfolio %s on date %s",
                    split_tx.id,
                    portfolio.id,
                    action.ex_date,
                )

            # --- Process BONUS ISSUE ---
            elif action.action_type.upper() == "BONUS":
                num = action.ratio_numerator or Decimal("1")
                den = action.ratio_denominator or Decimal("1")
                if num <= Decimal("0") or den <= Decimal("0"):
                    continue

                bonus_tx_in = schemas.TransactionCreate(
                    asset_id=asset.id,
                    portfolio_id=portfolio.id,
                    transaction_type=TransactionType.BONUS,
                    quantity=num,
                    price_per_unit=den,
                    fees=Decimal("0.0"),
                    transaction_date=datetime.combine(action.ex_date, time(0, 0)),
                    details={
                        "action": "BONUS_ISSUE",
                        "bonus_ratio": f"{num}:{den}",
                        "source": action.source,
                        "is_automated": True,
                    },
                )
                bonus_tx = crud.crud_corporate_action.handle_bonus_issue(
                    db=db,
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    transaction_in=bonus_tx_in,
                )
                bonus_tx.is_automated = True
                db.add(bonus_tx)
                db.flush()

                event = CorporateActionEvent(
                    user_id=portfolio.user_id,
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    transaction_id=bonus_tx.id,
                    event_type="BONUS",
                    event_date=action.ex_date,
                    units=holding_qty,
                    amount=Decimal("0.00"),
                    status="NEW",
                    details={
                        "stock_name": asset.name,
                        "symbol": asset.ticker_symbol,
                        "bonus_ratio": f"{num}:{den}",
                        "source": action.source,
                    },
                )
                db.add(event)
                db.flush()
                created_events.append(event)
                logger.info(
                    "Created automated BONUS transaction %s for portfolio %s on date %s",
                    bonus_tx.id,
                    portfolio.id,
                    action.ex_date,
                )

    db.commit()
    logger.info("Stock corporate action processing completed. Total events created: %d", len(created_events))
    return created_events
