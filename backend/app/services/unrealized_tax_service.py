import logging
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crud
from app.models import Asset, Transaction, TransactionLink
from app.schemas.capital_gains import UnrealizedGainsSummary, UnrealizedTaxLot
from app.schemas.enums import TransactionType
from app.services.capital_gains_service import (
    DATE_2018_01_31,
    HOLDING_PERIOD_EQUITY_LTCG,
    HOLDING_PERIOD_GENERAL_LTCG_NEW,
    CapitalGainsService,
)
from app.services.financial_data_service import financial_data_service

logger = logging.getLogger(__name__)

SECTION_112A_EXEMPTION_LIMIT = Decimal("125000.00")

EQUITY_ASSET_TYPES = {
    "STOCKS",
    "STOCK",
    "EQUITY",
    "MUTUAL_FUND_EQUITY",
    "ETF",
    "INDIAN_STOCKS",
    "MF_EQUITY",
    "EQUITY_LISTED",
}


def _safe_decimal(val, default: Decimal = Decimal("0.0")) -> Decimal:
    if val is None:
        return default
    try:
        d = Decimal(str(val))
        if d.is_nan() or d.is_infinite():
            return default
        return d
    except (InvalidOperation, ValueError, TypeError):
        return default


def _is_equity_type(asset_type_str: str, tax_rate: str = "") -> bool:
    cat = (asset_type_str or "").upper()
    return cat in EQUITY_ASSET_TYPES or "112A" in tax_rate or "111A" in tax_rate


class UnrealizedTaxService:
    def __init__(self, db: Session):
        self.db = db

    def _get_current_fy(self) -> str:
        today = date.today()
        year = today.year
        if today.month >= 4:
            return f"{year}-{str(year + 1)[-2:]}"
        else:
            return f"{year - 1}-{str(year)[-2:]}"

    def calculate_unrealized_gains(
        self,
        user_id: str,
        fy_year: Optional[str] = None,
        portfolio_id: Optional[str] = None,
        slab_rate: float = 30.0,
    ) -> UnrealizedGainsSummary:
        """
        Calculate unrealized capital gains and Section 112A exemption headroom
        across active holdings and open buy tax lots.
        """
        if not fy_year:
            fy_year = self._get_current_fy()

        # 1. Fetch Realized Capital Gains for FY to compute 112A Exemption Headroom
        cg_service = CapitalGainsService(self.db)
        realized_112a_ltcg = Decimal("0.0")
        try:
            realized_summary = cg_service.calculate_capital_gains(
                portfolio_id=portfolio_id,
                fy_year=fy_year,
                slab_rate=slab_rate,
                user_id=user_id,
            )
            for g in realized_summary.gains:
                currency_val = getattr(g, "currency", "INR") or "INR"
                is_foreign_gain = currency_val != "INR"
                is_domestic_equity = (
                    _is_equity_type(g.asset_type, g.tax_rate) and not is_foreign_gain
                )
                if g.gain_type == "LTCG" and is_domestic_equity and g.gain > Decimal("0.0"):
                    realized_112a_ltcg += _safe_decimal(g.gain)
        except Exception as exc:
            logger.error("Error calculating realized capital gains baseline for FY %s: %s", fy_year, exc)

        section_112a_realized_used = min(
            SECTION_112A_EXEMPTION_LIMIT, max(Decimal("0.0"), realized_112a_ltcg)
        )
        remaining_headroom = max(
            Decimal("0.0"), SECTION_112A_EXEMPTION_LIMIT - section_112a_realized_used
        )

        # 2. Query ALL BUY transactions for user/portfolio
        buy_tx_query = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type.in_(
                [
                    TransactionType.BUY,
                    TransactionType.ESPP_PURCHASE,
                    TransactionType.RSU_VEST,
                    TransactionType.BONUS,
                ]
            ),
        )
        if portfolio_id:
            buy_tx_query = buy_tx_query.where(Transaction.portfolio_id == portfolio_id)

        buy_txs = self.db.scalars(buy_tx_query).all()

        if not buy_txs:
            return UnrealizedGainsSummary(
                financial_year=fy_year,
                section_112a_realized_used=section_112a_realized_used,
                section_112a_remaining_headroom=remaining_headroom,
            )

        # Query all TransactionLinks for these buy txs to find sold quantities
        buy_tx_ids = [tx.id for tx in buy_txs]
        sold_qty_by_buy_tx = defaultdict(Decimal)
        if buy_tx_ids:
            links = self.db.scalars(
                select(TransactionLink).where(
                    TransactionLink.buy_transaction_id.in_(buy_tx_ids)
                )
            ).all()
            for link in links:
                sold_qty_by_buy_tx[link.buy_transaction_id] += _safe_decimal(link.quantity)

        today = date.today()
        lots: List[UnrealizedTaxLot] = []

        total_unrealized_stcg = Decimal("0.0")
        total_unrealized_ltcg = Decimal("0.0")
        section_112a_unrealized_eligible = Decimal("0.0")

        slab_decimal = Decimal(str(slab_rate)) / Decimal("100.0")

        # Process each buy transaction to calculate remaining open lot
        for tx in buy_txs:
            buy_qty = _safe_decimal(tx.quantity)
            sold_qty = sold_qty_by_buy_tx.get(tx.id, Decimal("0.0"))
            rem_qty = buy_qty - sold_qty

            if rem_qty <= Decimal("0.0001"):
                continue

            asset = tx.asset
            if not asset:
                continue

            asset_cat = (
                asset.asset_type.value
                if hasattr(asset.asset_type, "value")
                else str(asset.asset_type)
            ).upper()

            buy_price = _safe_decimal(tx.price_per_unit)
            current_price = buy_price

            # Determine current market price
            if asset.ticker_symbol:
                try:
                    prices_res = financial_data_service.get_current_prices(
                        [{"ticker_symbol": asset.ticker_symbol, "asset_type": asset_cat}]
                    )
                    live_val = (prices_res.get(asset.ticker_symbol) or {}).get("current_price")
                    if live_val is not None:
                        parsed_live = _safe_decimal(live_val)
                        if parsed_live > Decimal("0.0"):
                            current_price = parsed_live
                except Exception as exc:
                    logger.warning("Error fetching market price for asset %s: %s", asset.ticker_symbol, exc)

            total_cost = buy_price * rem_qty
            market_value = current_price * rem_qty
            unrealized_gain = market_value - total_cost

            # Compute holding days
            tx_date = (
                tx.transaction_date.date()
                if isinstance(tx.transaction_date, datetime)
                else tx.transaction_date
            )
            holding_days = (today - tx_date).days

            # Determine STCG vs LTCG
            is_foreign = bool(asset.currency and asset.currency != "INR")
            is_domestic_equity = _is_equity_type(asset_cat) and not is_foreign

            is_grandfathered = False
            if is_domestic_equity and tx_date <= DATE_2018_01_31:
                is_grandfathered = True

            if is_domestic_equity:
                gain_type = (
                    "LTCG" if holding_days > HOLDING_PERIOD_EQUITY_LTCG else "STCG"
                )
                tax_rate = (
                    "LTCG 12.5% (Sec 112A)"
                    if gain_type == "LTCG"
                    else "STCG 20% (Sec 111A)"
                )
            else:
                gain_type = (
                    "LTCG" if holding_days > HOLDING_PERIOD_GENERAL_LTCG_NEW else "STCG"
                )
                if is_foreign and gain_type == "LTCG":
                    tax_rate = "LTCG 12.5% (Foreign)"
                elif gain_type == "LTCG":
                    tax_rate = "LTCG 12.5%"
                else:
                    tax_rate = f"Slab ({slab_rate}%)"

            # Calculate estimated lot tax
            lot_tax = Decimal("0.0")
            if unrealized_gain > Decimal("0.0"):
                if gain_type == "STCG":
                    total_unrealized_stcg += unrealized_gain
                    if "20%" in tax_rate:
                        lot_tax = unrealized_gain * Decimal("0.20")
                    elif "15%" in tax_rate:
                        lot_tax = unrealized_gain * Decimal("0.15")
                    else:
                        lot_tax = unrealized_gain * slab_decimal
                else:
                    total_unrealized_ltcg += unrealized_gain
                    if is_domestic_equity:
                        section_112a_unrealized_eligible += unrealized_gain
                        lot_tax = Decimal("0.0")
                    else:
                        lot_tax = unrealized_gain * Decimal("0.125")
            else:
                if gain_type == "STCG":
                    total_unrealized_stcg += unrealized_gain
                else:
                    total_unrealized_ltcg += unrealized_gain

            lots.append(
                UnrealizedTaxLot(
                    holding_id=str(tx.id),
                    asset_id=str(asset.id),
                    asset_ticker=asset.ticker_symbol or asset.name,
                    asset_name=asset.name,
                    asset_type=asset_cat,
                    buy_date=tx_date,
                    quantity=rem_qty,
                    buy_price=buy_price,
                    current_price=current_price,
                    total_cost=total_cost,
                    market_value=market_value,
                    unrealized_gain=unrealized_gain,
                    gain_type=gain_type,
                    holding_days=holding_days,
                    tax_rate=tax_rate,
                    estimated_tax=lot_tax,
                    is_grandfathered=is_grandfathered,
                    is_foreign=is_foreign,
                    currency=asset.currency or "INR",
                )
            )

        # 3. Section 112A Exemption Pooling Math
        unrealized_exemption_used = min(
            remaining_headroom, max(Decimal("0.0"), section_112a_unrealized_eligible)
        )
        taxable_112a_unrealized_ltcg = max(
            Decimal("0.0"), section_112a_unrealized_eligible - unrealized_exemption_used
        )
        estimated_unrealized_112a_ltcg_tax = taxable_112a_unrealized_ltcg * Decimal(
            "0.125"
        )

        estimated_unrealized_ltcg_tax = estimated_unrealized_112a_ltcg_tax + sum(
            lot.estimated_tax
            for lot in lots
            if lot.gain_type == "LTCG" and "112A" not in lot.tax_rate
        )

        estimated_unrealized_stcg_tax = sum(
            lot.estimated_tax for lot in lots if lot.gain_type == "STCG"
        )
        total_estimated_tax = estimated_unrealized_stcg_tax + estimated_unrealized_ltcg_tax

        return UnrealizedGainsSummary(
            financial_year=fy_year,
            total_unrealized_stcg=total_unrealized_stcg,
            total_unrealized_ltcg=total_unrealized_ltcg,
            total_unrealized_gain=total_unrealized_stcg + total_unrealized_ltcg,
            section_112a_realized_used=section_112a_realized_used,
            section_112a_remaining_headroom=remaining_headroom,
            section_112a_unrealized_eligible=section_112a_unrealized_eligible,
            section_112a_unrealized_exemption_used=unrealized_exemption_used,
            estimated_unrealized_stcg_tax=estimated_unrealized_stcg_tax,
            estimated_unrealized_ltcg_tax=estimated_unrealized_ltcg_tax,
            total_estimated_tax=total_estimated_tax,
            lots=sorted(lots, key=lambda l: l.buy_date),
        )
