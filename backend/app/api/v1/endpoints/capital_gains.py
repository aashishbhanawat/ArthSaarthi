from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.capital_gains import CapitalGainsSummary
from app.services.capital_gains_service import CapitalGainsService

router = APIRouter()


@router.get("/", response_model=CapitalGainsSummary)
def get_capital_gains(
    fy: str = Query(..., description="Financial Year (e.g., '2025-26')"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    slab_rate: float = Query(
        30.0, description="User's Income Tax Slab Rate (e.g. 30.0)"
    ),
    db: Session = Depends(get_db),
):
    """
    Get Capital Gains Report for a specific Financial Year.

    Returns:
    - Summary of STCG and LTCG
    - ITR-2 Schedule CG Matrix (5 periods x 4 categories)
    - Schedule 112A Entries (Grandfathered Equity)
    - Detailed list of all realized gains
    """
    service = CapitalGainsService(db)
    return service.calculate_capital_gains(
        portfolio_id=portfolio_id, fy_year=fy, slab_rate=slab_rate
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
):
    """
    Export Capital Gains as a CSV file for download.
    """
    service = CapitalGainsService(db)
    summary = service.calculate_capital_gains(
        portfolio_id=portfolio_id, fy_year=fy, slab_rate=slab_rate
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
