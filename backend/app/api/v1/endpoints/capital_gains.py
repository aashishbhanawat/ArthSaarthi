import logging
from io import StringIO
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import crud
from app.core import dependencies as deps
from app.db.session import get_db
from app.models import User
from app.schemas.capital_gains import (
    CapitalGainsSummary,
    CapitalLossLedgerCreate,
    CapitalLossLedgerResponse,
    CapitalLossLedgerUpdate,
    CapitalSetOffSummaryResponse,
    TaxLossHarvestingSummary,
    UnrealizedGainsSummary,
)
from app.services.capital_gains_service import CapitalGainsService
from app.services.tax_setoff_service import TaxSetOffService
from app.services.unrealized_tax_service import UnrealizedTaxService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=CapitalGainsSummary)
def get_capital_gains(
    fy: str = Query(..., description="Financial Year (e.g., '2025-26')"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    slab_rate: float = Query(
        30.0, description="User's Income Tax Slab Rate (e.g. 30.0)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get Capital Gains Report for a specific Financial Year.

    Returns:
    - Summary of STCG and LTCG
    - ITR-2 Schedule CG Matrix (5 periods x 4 categories)
    - Schedule 112A Entries (Grandfathered Equity)
    - Detailed list of all realized gains
    """
    if portfolio_id:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if portfolio.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    service = CapitalGainsService(db)
    return service.calculate_capital_gains(
        portfolio_id=portfolio_id,
        user_id=str(current_user.id),
        fy_year=fy,
        slab_rate=slab_rate,
    )


@router.get("/export")
def export_capital_gains_csv(
    fy: str = Query(..., description="Financial Year (e.g., '2025-26')"),
    report_type: str = Query("gains", description="Type of report: 'gains' or '112a'"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    slab_rate: float = Query(
        30.0, description="User's Income Tax Slab Rate (e.g. 30.0)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Export Capital Gains as a CSV file for download.
    """
    if portfolio_id:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if portfolio.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    service = CapitalGainsService(db)
    summary = service.calculate_capital_gains(
        portfolio_id=portfolio_id,
        user_id=str(current_user.id),
        fy_year=fy,
        slab_rate=slab_rate,
    )

    # Build CSV content
    output = StringIO()

    if report_type == "112a":
        # Header for Schedule 112A
        output.write(
            "ISIN,Asset Name,Quantity,Sale Price per Unit,"
            "Full Value Consideration,Cost of Acquisition Orig,"
            "FMV 31 Jan 2018,Total FMV,Cost of Acquisition Final,"
            "Expenditure,Total Deductions,Balance\n"
        )
        for row in summary.schedule_112a:
            output.write(
                f'"{row.isin}","{row.asset_name}",{row.quantity},{row.sale_price},'
                f"{row.full_value_consideration},{row.cost_of_acquisition_orig},"
                f"{row.fmv_31jan2018 or ''},{row.total_fmv or ''},"
                f"{row.cost_of_acquisition_final},"
                f"{row.expenditure},{row.total_deductions},{row.balance}\n"
            )
        filename = f"schedule_112a_{fy.replace('-', '_')}.csv"

    else:
        # Default: Realized Gains
        # Header
        output.write(
            "Asset,Type,Buy Date,Sell Date,Qty,Buy Price,Sell Price,"
            "Buy Value,Sell Value,Gain/Loss,Gain Type,Tax Rate,Grandfathered\n"
        )
        # Rows
        for g in summary.gains:
            output.write(
                f'"{g.asset_ticker}","{g.asset_type}",{g.buy_date},{g.sell_date},'
                f"{g.quantity},{g.buy_price},{g.sell_price},"
                f"{g.total_buy_value},{g.total_sell_value},{g.gain},"
                f'"{g.gain_type}","{g.tax_rate}",{g.is_grandfathered}\n'
            )
        filename = f"capital_gains_{fy.replace('-', '_')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/unrealized", response_model=UnrealizedGainsSummary)
def get_unrealized_capital_gains(
    fy: Optional[str] = Query(None, description="Financial Year (e.g., '2025-26')"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    slab_rate: float = Query(
        30.0, description="User's Income Tax Slab Rate (e.g. 30.0)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get Unrealized Capital Gains and Section 112A Exemption Headroom.
    """
    if portfolio_id:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if portfolio.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        service = UnrealizedTaxService(db)
        return service.calculate_unrealized_gains(
            user_id=str(current_user.id),
            fy_year=fy,
            portfolio_id=portfolio_id,
            slab_rate=slab_rate,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Error calculating unrealized capital gains: %s", exc, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate unrealized capital gains: {str(exc)}",
        )


@router.get("/set-off", response_model=CapitalSetOffSummaryResponse)
def get_capital_gains_setoff(
    fy: str = Query(..., description="Financial Year (e.g., '2025-26')"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    slab_rate: float = Query(
        30.0, description="User's Income Tax Slab Rate (e.g. 30.0)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get Net Capital Gains after statutory intra-head set-off
    and brought-forward loss ledger offset.
    """
    if portfolio_id:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if portfolio.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    service = TaxSetOffService(db)
    return service.calculate_net_capital_gains(
        user_id=str(current_user.id),
        fy_year=fy,
        portfolio_id=portfolio_id,
        slab_rate=slab_rate,
    )


@router.get("/loss-ledger", response_model=List[CapitalLossLedgerResponse])
def get_loss_ledger_entries(
    fy: str = Query(
        "2025-26", description="Current Financial Year for countdown calculation"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get user's brought-forward capital loss ledger entries with 8-year countdown meters.
    """
    service = TaxSetOffService(db)
    return service.get_loss_ledger_entries(
        user_id=str(current_user.id), current_fy=fy
    )


@router.post("/loss-ledger", response_model=CapitalLossLedgerResponse)
def create_loss_ledger_entry(
    entry_in: CapitalLossLedgerCreate,
    current_fy: str = Query("2025-26", description="Current Financial Year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create a new brought-forward capital loss ledger entry.
    """
    existing = crud.capital_loss_ledger.get_by_owner_and_ay(
        db, user_id=current_user.id, assessment_year=entry_in.assessment_year
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Loss ledger record for Assessment Year {entry_in.assessment_year} "
                f"already exists."
            ),
        )

    db_obj = crud.capital_loss_ledger.create_with_owner(
        db, obj_in=entry_in, user_id=current_user.id
    )
    service = TaxSetOffService(db)
    entries = service.get_loss_ledger_entries(
        user_id=str(current_user.id), current_fy=current_fy
    )
    for e in entries:
        if e.id == str(db_obj.id):
            return e
    return CapitalLossLedgerResponse.from_orm(db_obj)


@router.put("/loss-ledger/{ledger_id}", response_model=CapitalLossLedgerResponse)
def update_loss_ledger_entry(
    ledger_id: str,
    entry_in: CapitalLossLedgerUpdate,
    current_fy: str = Query("2025-26", description="Current Financial Year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update an existing brought-forward capital loss ledger entry.
    """
    db_obj = crud.capital_loss_ledger.get(db, id=ledger_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Loss ledger entry not found")
    if db_obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_obj = crud.capital_loss_ledger.update(db, db_obj=db_obj, obj_in=entry_in)
    service = TaxSetOffService(db)
    entries = service.get_loss_ledger_entries(
        user_id=str(current_user.id), current_fy=current_fy
    )
    for e in entries:
        if e.id == str(db_obj.id):
            return e
    return CapitalLossLedgerResponse.from_orm(db_obj)



@router.delete("/loss-ledger/{ledger_id}")
def delete_loss_ledger_entry(
    ledger_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete a brought-forward capital loss ledger entry.
    """
    db_obj = crud.capital_loss_ledger.get(db, id=ledger_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Loss ledger entry not found")
    if db_obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    crud.capital_loss_ledger.remove(db, id=ledger_id)
    return {"message": "Loss ledger entry deleted successfully"}


@router.get("/tax-loss-harvesting", response_model=TaxLossHarvestingSummary)
def get_tax_loss_harvesting_opportunities(
    fy: str = Query(..., description="Financial Year (e.g., '2025-26')"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    slab_rate: float = Query(
        30.0, description="User's Income Tax Slab Rate (e.g. 30.0)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get Tax-Loss Harvesting recommendations for open tax lots.
    """
    if portfolio_id:
        portfolio = crud.portfolio.get(db=db, id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if portfolio.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    service = TaxSetOffService(db)
    return service.get_loss_harvesting_opportunities(
        user_id=str(current_user.id),
        fy_year=fy,
        portfolio_id=portfolio_id,
        slab_rate=slab_rate,
    )


