import logging
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.models.capital_loss_ledger import CapitalLossLedger
from app.schemas.capital_gains import (
    CapitalLossLedgerResponse,
    CapitalSetOffSummaryResponse,
    SetOffBreakdown,
    TaxLossHarvestingItem,
    TaxLossHarvestingSummary,
)
from app.services.capital_gains_service import CapitalGainsService
from app.services.unrealized_tax_service import UnrealizedTaxService

logger = logging.getLogger(__name__)


def parse_fy(fy_str: str) -> Tuple[int, int]:
    """Parses '2025-26' into start_year=2025, end_year=26"""
    parts = fy_str.split("-")
    start = int(parts[0])
    end = int(parts[1]) if len(parts) > 1 else (start + 1) % 100
    return start, end


def fy_to_ay(fy_str: str) -> str:
    """Converts FY '2025-26' to AY '2026-27'"""
    start, end = parse_fy(fy_str)
    ay_start = start + 1
    ay_end = (end + 1) % 100
    return f"{ay_start}-{ay_end:02d}"


def calculate_years_remaining(loss_ay: str, current_ay: str) -> int:
    """
    Calculates remaining years out of 8-year statutory limit.
    Loss from AY 2020-21 evaluated in AY 2026-27:
    Loss start year: 2020. Expiry AY: 2020 + 8 = 2028 (AY 2028-29).
    Current AY start year: 2026.
    Years remaining: (2020 + 8) - 2026 = 2 years remaining.
    """
    loss_start, _ = parse_fy(loss_ay)
    curr_start, _ = parse_fy(current_ay)
    expiry_year = loss_start + 8
    return expiry_year - curr_start


class TaxSetOffService:
    def __init__(self, db: Session):
        self.db = db

    def get_loss_ledger_entries(
        self, user_id: Union[str, uuid.UUID], current_fy: str
    ) -> List[CapitalLossLedgerResponse]:
        """Fetches all loss ledger entries for user with countdown meters."""
        current_ay = fy_to_ay(current_fy)
        user_uuid = (
            uuid.UUID(str(user_id))
            if isinstance(user_id, (str, uuid.UUID))
            else user_id
        )
        entries = (
            self.db.query(CapitalLossLedger)
            .filter(CapitalLossLedger.user_id == user_uuid)
            .order_by(CapitalLossLedger.assessment_year.asc())
            .all()
        )

        result = []
        for e in entries:
            remaining = calculate_years_remaining(e.assessment_year, current_ay)
            is_expired = remaining < 0
            result.append(
                CapitalLossLedgerResponse(
                    id=str(e.id),
                    user_id=str(e.user_id),
                    financial_year=e.financial_year,
                    assessment_year=e.assessment_year,
                    stcl_amount=Decimal(str(e.stcl_amount)),
                    ltcl_amount=Decimal(str(e.ltcl_amount)),
                    is_itr_filed_on_time=e.is_itr_filed_on_time,
                    notes=e.notes,
                    years_remaining=max(0, remaining),
                    is_expired=is_expired,
                )
            )
        return result

    def calculate_net_capital_gains(
        self,
        user_id: str,
        fy_year: str,
        portfolio_id: Optional[str] = None,
        slab_rate: float = 30.0,
    ) -> CapitalSetOffSummaryResponse:
        """
        Executes Section 70, 71, and 74 intra-head capital loss set-off logic.
        """
        current_ay = fy_to_ay(fy_year)
        cg_service = CapitalGainsService(self.db)
        summary = cg_service.calculate_capital_gains(
            portfolio_id=portfolio_id,
            user_id=user_id,
            fy_year=fy_year,
            slab_rate=slab_rate,
        )

        gross_stcg = Decimal("0.0")
        gross_stcl = Decimal("0.0")
        gross_ltcg = Decimal("0.0")
        gross_ltcl = Decimal("0.0")

        for g in summary.gains:
            if g.gain_type == "STCG":
                if g.gain >= 0:
                    gross_stcg += Decimal(str(g.gain))
                else:
                    gross_stcl += abs(Decimal(str(g.gain)))
            elif g.gain_type == "LTCG":
                if g.gain >= 0:
                    gross_ltcg += Decimal(str(g.gain))
                else:
                    gross_ltcl += abs(Decimal(str(g.gain)))

        # Step A: Current Year Intra-Head Set-off (Section 70)
        # 1. CY STCL set off against CY STCG
        cy_stcl_offset_against_stcg = min(gross_stcl, gross_stcg)
        rem_stcg = gross_stcg - cy_stcl_offset_against_stcg
        rem_stcl = gross_stcl - cy_stcl_offset_against_stcg

        # 2. Remaining CY STCL set off against CY LTCG
        cy_stcl_offset_against_ltcg = min(rem_stcl, gross_ltcg)
        rem_ltcg = gross_ltcg - cy_stcl_offset_against_ltcg
        rem_stcl = rem_stcl - cy_stcl_offset_against_ltcg

        # 3. CY LTCL set off against remaining CY LTCG ONLY (Section 70(3))
        cy_ltcl_offset_against_ltcg = min(gross_ltcl, rem_ltcg)
        rem_ltcg = rem_ltcg - cy_ltcl_offset_against_ltcg
        rem_ltcl = gross_ltcl - cy_ltcl_offset_against_ltcg

        # Step B: Brought-Forward Loss Set-off (Section 74)
        ledger_entries = self.get_loss_ledger_entries(user_id, fy_year)

        total_bf_stcl = Decimal("0.0")
        total_bf_ltcl = Decimal("0.0")

        # Eligible brought-forward losses (strictly prior AY, filed on time, active)
        for entry in ledger_entries:
            entry_start, _ = parse_fy(entry.assessment_year)
            curr_start, _ = parse_fy(current_ay)
            if (
                entry_start < curr_start
                and entry.is_itr_filed_on_time
                and not entry.is_expired
            ):
                total_bf_stcl += entry.stcl_amount
                total_bf_ltcl += entry.ltcl_amount

        # 1. BF STCL set off against remaining STCG
        bf_stcl_offset_stcg = min(total_bf_stcl, rem_stcg)
        rem_stcg -= bf_stcl_offset_stcg
        rem_bf_stcl = total_bf_stcl - bf_stcl_offset_stcg

        # 2. Remaining BF STCL set off against remaining LTCG
        bf_stcl_offset_ltcg = min(rem_bf_stcl, rem_ltcg)
        rem_ltcg -= bf_stcl_offset_ltcg
        rem_bf_stcl -= bf_stcl_offset_ltcg

        bf_stcl_used = bf_stcl_offset_stcg + bf_stcl_offset_ltcg
        unabsorbed_bf_stcl = total_bf_stcl - bf_stcl_used

        # 3. BF LTCL set off against remaining LTCG ONLY
        bf_ltcl_used = min(total_bf_ltcl, rem_ltcg)
        rem_ltcg -= bf_ltcl_used
        unabsorbed_bf_ltcl = total_bf_ltcl - bf_ltcl_used

        # Step C: Net Tax Computations
        # Use actual effective STCG rate from CapitalGainsService
        # (e.g., 20% for Equity 111A vs slab rate)
        estimated_stcg_tax = getattr(summary, "estimated_stcg_tax", Decimal("0.0"))

        if gross_stcg > 0 and estimated_stcg_tax > 0:
            stcg_tax_rate = estimated_stcg_tax / gross_stcg
        else:
            stcg_tax_rate = Decimal(str(slab_rate)) / Decimal("100.0")

        gross_stcg_tax = gross_stcg * stcg_tax_rate
        # Section 112A headroom: LTCG exemption threshold 1.25L (125000)
        exemption_112a = Decimal("125000.00")
        taxable_gross_ltcg = max(Decimal("0.0"), gross_ltcg - exemption_112a)
        gross_ltcg_tax = taxable_gross_ltcg * Decimal("0.125")
        gross_estimated_tax = gross_stcg_tax + gross_ltcg_tax

        # Net estimated tax after set-off
        net_stcg_tax = rem_stcg * stcg_tax_rate
        taxable_net_ltcg = max(Decimal("0.0"), rem_ltcg - exemption_112a)
        net_ltcg_tax = taxable_net_ltcg * Decimal("0.125")
        net_estimated_tax = net_stcg_tax + net_ltcg_tax

        tax_saved_via_setoff = max(
            Decimal("0.0"), gross_estimated_tax - net_estimated_tax
        )

        breakdown = SetOffBreakdown(
            gross_stcg=gross_stcg,
            gross_stcl=gross_stcl,
            gross_ltcg=gross_ltcg,
            gross_ltcl=gross_ltcl,
            cy_stcl_offset_against_stcg=cy_stcl_offset_against_stcg,
            cy_stcl_offset_against_ltcg=cy_stcl_offset_against_ltcg,
            cy_ltcl_offset_against_ltcg=cy_ltcl_offset_against_ltcg,
            bf_stcl_used=bf_stcl_used,
            bf_ltcl_used=bf_ltcl_used,
            net_taxable_stcg=rem_stcg,
            net_taxable_ltcg=rem_ltcg,
            unabsorbed_stcl_to_carry_forward=rem_stcl + unabsorbed_bf_stcl,
            unabsorbed_ltcl_to_carry_forward=rem_ltcl + unabsorbed_bf_ltcl,
            gross_estimated_tax=gross_estimated_tax,
            net_estimated_tax=net_estimated_tax,
            tax_saved_via_setoff=tax_saved_via_setoff,
        )

        return CapitalSetOffSummaryResponse(
            financial_year=fy_year,
            assessment_year=current_ay,
            breakdown=breakdown,
            loss_ledger_entries=ledger_entries,
        )

    def get_loss_harvesting_opportunities(
        self,
        user_id: str,
        fy_year: str,
        portfolio_id: Optional[str] = None,
        slab_rate: float = 30.0,
    ) -> TaxLossHarvestingSummary:
        """
        Scans unsold tax lots with negative unrealized gains
        and computes potential tax savings.
        """
        # Get net taxable gains before harvesting
        setoff_summary = self.calculate_net_capital_gains(
            user_id=user_id,
            fy_year=fy_year,
            portfolio_id=portfolio_id,
            slab_rate=slab_rate,
        )
        net_stcg = setoff_summary.breakdown.net_taxable_stcg
        net_ltcg = setoff_summary.breakdown.net_taxable_ltcg
        rem_taxable_stcg = net_stcg
        # Section 112A exemption: LTCG below 1.25L has ₹0 tax
        exemption_112a = Decimal("125000.00")
        rem_taxable_ltcg = max(
            Decimal("0.0"),
            net_ltcg - exemption_112a,
        )

        # Compute effective STCG rate for loss harvesting
        cg_service = CapitalGainsService(self.db)
        cg_summary = cg_service.calculate_capital_gains(
            portfolio_id=portfolio_id,
            user_id=user_id,
            fy_year=fy_year,
            slab_rate=slab_rate,
        )
        est_stcg_tax = getattr(cg_summary, "estimated_stcg_tax", Decimal("0.0"))
        tot_stcg = getattr(cg_summary, "total_stcg", Decimal("0.0"))
        if tot_stcg > 0 and est_stcg_tax > 0:
            stcg_tax_rate = est_stcg_tax / tot_stcg
        else:
            stcg_tax_rate = Decimal(str(slab_rate)) / Decimal("100.0")


        # Fetch open lots
        unrealized_service = UnrealizedTaxService(self.db)
        unrealized_summary = unrealized_service.calculate_unrealized_gains(
            user_id=user_id,
            fy_year=fy_year,
            portfolio_id=portfolio_id,
            slab_rate=slab_rate,
        )

        total_harvestable_stcl = Decimal("0.0")
        total_harvestable_ltcl = Decimal("0.0")
        total_potential_tax_savings = Decimal("0.0")
        items: List[TaxLossHarvestingItem] = []

        for lot in unrealized_summary.lots:
            if lot.unrealized_gain < 0:
                unrealized_loss = abs(lot.unrealized_gain)
                is_stcl = lot.gain_type == "STCG"
                loss_type = "STCL" if is_stcl else "LTCL"

                if is_stcl:
                    total_harvestable_stcl += unrealized_loss
                    if rem_taxable_stcg > 0:
                        offset_amount = min(unrealized_loss, rem_taxable_stcg)
                        tax_saved = offset_amount * stcg_tax_rate
                        rem_taxable_stcg -= offset_amount
                        stcg_rate_pct = (stcg_tax_rate * Decimal("100.0")).quantize(
                            Decimal("0.1")
                        )
                        reason = (
                            f"Harvest ₹{unrealized_loss:,.2f} STCL to offset "
                            f"taxable STCG. Saves ~₹{tax_saved:,.2f} tax at "
                            f"{stcg_rate_pct}% rate."
                        )
                    elif rem_taxable_ltcg > 0:

                        offset_amount = min(unrealized_loss, rem_taxable_ltcg)
                        tax_saved = offset_amount * Decimal("0.125")
                        rem_taxable_ltcg -= offset_amount
                        reason = (
                            f"Harvest ₹{unrealized_loss:,.2f} STCL to offset "
                            f"taxable LTCG. Saves ~₹{tax_saved:,.2f} tax at "
                            f"12.5% rate."
                        )
                    else:
                        tax_saved = Decimal("0.0")
                        reason = (
                            f"Harvest ₹{unrealized_loss:,.2f} STCL to carry "
                            f"forward for up to 8 years to offset future "
                            f"capital gains."
                        )
                else:
                    total_harvestable_ltcl += unrealized_loss
                    if rem_taxable_ltcg > 0:
                        offset_amount = min(unrealized_loss, rem_taxable_ltcg)
                        tax_saved = offset_amount * Decimal("0.125")
                        rem_taxable_ltcg -= offset_amount
                        reason = (
                            f"Harvest ₹{unrealized_loss:,.2f} LTCL to offset "
                            f"taxable LTCG. Saves ~₹{tax_saved:,.2f} tax at "
                            f"12.5% rate."
                        )
                    else:
                        tax_saved = Decimal("0.0")
                        reason = (
                            f"Harvest ₹{unrealized_loss:,.2f} LTCL to carry "
                            f"forward for up to 8 years to offset future LTCG."
                        )

                total_potential_tax_savings += tax_saved


                items.append(
                    TaxLossHarvestingItem(
                        holding_id=lot.holding_id,
                        asset_id=lot.asset_id,
                        asset_ticker=lot.asset_ticker,
                        asset_name=lot.asset_name,
                        asset_type=lot.asset_type,
                        buy_date=lot.buy_date,
                        quantity=lot.quantity,
                        buy_price=lot.buy_price,
                        current_price=lot.current_price,
                        total_cost=lot.total_cost,
                        market_value=lot.market_value,
                        unrealized_loss=unrealized_loss,
                        loss_type=loss_type,
                        holding_days=lot.holding_days,
                        potential_tax_saved=tax_saved,
                        recommended_sell_quantity=lot.quantity,
                        recommendation_reason=reason,
                    )
                )

        # Sort opportunities by potential tax saved descending, then loss amount
        items.sort(
            key=lambda x: (x.potential_tax_saved, x.unrealized_loss), reverse=True
        )

        return TaxLossHarvestingSummary(
            financial_year=fy_year,
            total_harvestable_stcl=total_harvestable_stcl,
            total_harvestable_ltcl=total_harvestable_ltcl,
            total_potential_tax_savings=total_potential_tax_savings,
            net_taxable_stcg_before_harvesting=net_stcg,
            net_taxable_ltcg_before_harvesting=net_ltcg,
            harvesting_opportunities=items,
        )
