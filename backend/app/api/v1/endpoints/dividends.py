import csv
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dividends import DividendSummary
from app.services.dividend_service import DividendService

router = APIRouter()

@router.get("/", response_model=DividendSummary)
def get_dividend_report(
    fy: str = Query(..., description="Financial Year (e.g., '2025-26')"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    db: Session = Depends(get_db),
):
    """
    Get Dividend Report for a specific Financial Year.
    """
    service = DividendService(db)
    return service.get_dividend_report(fy_year=fy, portfolio_id=portfolio_id)

@router.get("/export")
def export_dividend_report_csv(
    fy: str = Query(..., description="Financial Year (e.g., '2025-26')"),
    portfolio_id: Optional[str] = Query(None, description="Filter by Portfolio ID"),
    db: Session = Depends(get_db),
):
    """
    Export Dividend Report as a CSV file for download.
    """
    service = DividendService(db)
    summary = service.get_dividend_report(fy_year=fy, portfolio_id=portfolio_id)

    output = StringIO()
    writer = csv.writer(output)

    # Write Disclaimer
    writer.writerow([
        "Disclaimer: This report is for informational purposes only. "
        "For foreign dividends, the INR conversion uses a proxy historical "
        "exchange rate. Please consult a tax professional and verify with "
        "actual SBI TTBR as per IT Rule 115."
    ])
    writer.writerow([]) # Empty row

    # Summary Header
    writer.writerow([
        "Advance Tax Bucket",
        "Total Dividends (INR)"
    ])

    # Summary Rows
    periods = [
        "Upto 15/6",
        "16/6 - 15/9",
        "16/9 - 15/12",
        "16/12 - 15/3",
        "16/3 - 31/3",
    ]
    for period in periods:
        writer.writerow([
            period,
            summary.bucket_totals.get(period, 0)
        ])

    writer.writerow([]) # Empty row

    # Detailed Header
    writer.writerow([
        "Asset Name",
        "Ticker/Symbol",
        "Date",
        "Quantity",
        "Amount (Native)",
        "Currency",
        "Proxy TTBR Date (Rule 115)",
        "Proxy TTBR Rate",
        "Amount (INR)",
        "Advance Tax Period"
    ])

    for entry in summary.entries:
        writer.writerow([
            entry.asset_name,
            entry.asset_ticker,
            entry.date,
            entry.quantity,
            entry.amount_native,
            entry.currency,
            entry.ttbr_date if entry.ttbr_date else "N/A",
            entry.ttbr_rate if entry.ttbr_rate else "N/A",
            entry.amount_inr,
            entry.period
        ])

    filename = f"dividend_report_{fy.replace('-', '_')}.csv"

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
