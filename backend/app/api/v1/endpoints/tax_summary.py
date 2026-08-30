import csv
import io
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from sqlalchemy.orm import Session

from app.core import dependencies as deps
from app.core.tax_rules_registry import MANDATORY_TAX_DISCLAIMER
from app.db.session import get_db
from app.models.user import User
from app.schemas.tax_summary import TaxSummaryResponse
from app.services.tax_regime_service import TaxRegimeService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=TaxSummaryResponse)
@router.get("/", response_model=TaxSummaryResponse)
def get_tax_summary(
    financial_year: str = Query("2024-25", description="FY (e.g. '2024-25')"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get consolidated Financial Year Tax Readiness summary report (FR16.4).
    Compares Old vs New Tax Regime with non-advisory legal disclaimer (FR16.4.1).
    """
    return TaxRegimeService.compute_tax_summary(
        db, user_id=current_user.id, financial_year=financial_year
    )


@router.get("/export/csv")
def export_tax_summary_csv(
    financial_year: str = Query("2024-25", description="FY (e.g. '2024-25')"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Export Tax Readiness Summary Report as CSV with mandatory legal disclaimer embedded.
    """
    summary = TaxRegimeService.compute_tax_summary(
        db, user_id=current_user.id, financial_year=financial_year
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Mandatory Legal Disclaimer Headers
    writer.writerow(["=== IMPORTANT LEGAL NOTICE & TAX DISCLAIMER ==="])
    writer.writerow([MANDATORY_TAX_DISCLAIMER])
    writer.writerow([
        "1. Calculations shown do NOT represent actual final tax liabilities "
        "payable to IT Department."
    ])
    writer.writerow([
        "2. For official tax filing, users MUST consult a qualified "
        "Chartered Accountant (CA)."
    ])
    writer.writerow([])  # Blank row separator

    writer.writerow(["Financial Year", summary.financial_year])
    writer.writerow(["Recommended Tax Regime", summary.recommended_regime])
    writer.writerow(["Estimated Tax Savings", f"INR {summary.tax_savings:,.2f}"])
    writer.writerow([])

    writer.writerow(["=== INCOME & EXEMPTIONS SUMMARY ==="])
    writer.writerow(
        ["Gross Salary", f"INR {summary.income_summary.gross_salary:,.2f}"]
    )
    writer.writerow(
        ["Business Income", f"INR {summary.income_summary.business_income:,.2f}"]
    )
    writer.writerow(
        ["Dividend Income", f"INR {summary.income_summary.dividend_income:,.2f}"]
    )
    writer.writerow(
        ["Other Income", f"INR {summary.income_summary.other_income:,.2f}"]
    )
    writer.writerow(
        ["Total Gross Income", f"INR {summary.income_summary.total_gross_income:,.2f}"]
    )
    writer.writerow(
        ["Total TDS Credits", f"INR {summary.income_summary.total_tds_credits:,.2f}"]
    )
    writer.writerow([])

    writer.writerow(["=== DEDUCTIONS SUMMARY (CHAPTER VI-A) ==="])
    writer.writerow(
        ["Section 80C", f"INR {summary.deduction_summary.section_80c:,.2f}"]
    )
    writer.writerow(
        ["Section 80D", f"INR {summary.deduction_summary.section_80d:,.2f}"]
    )
    writer.writerow(
        [
            "Section 80CCD(1B)",
            f"INR {summary.deduction_summary.section_80ccd_1b:,.2f}",
        ]
    )
    writer.writerow(
        ["Section 80E", f"INR {summary.deduction_summary.section_80e:,.2f}"]
    )
    writer.writerow(
        ["Section 80G", f"INR {summary.deduction_summary.section_80g:,.2f}"]
    )
    writer.writerow(
        [
            "Section 80TTA/80TTB",
            f"INR {summary.deduction_summary.section_80tta_80ttb:,.2f}",
        ]
    )
    writer.writerow(
        [
            "Total Chapter VI-A Deductions",
            f"INR {summary.deduction_summary.total_chapter_via_deductions:,.2f}",
        ]
    )
    writer.writerow([])

    writer.writerow(["=== DUAL REGIME COMPARISON ==="])
    writer.writerow([
        "Metric",
        "Old Tax Regime",
        "New Tax Regime (Sec 115BAC)",
    ])
    writer.writerow([
        "Gross Income",
        f"INR {summary.old_regime.gross_income:,.2f}",
        f"INR {summary.new_regime.gross_income:,.2f}",
    ])
    writer.writerow([
        "Standard Deduction",
        f"INR {summary.old_regime.exemptions:,.2f}",
        f"INR {summary.new_regime.exemptions:,.2f}",
    ])
    writer.writerow([
        "Chapter VI-A Deductions",
        f"INR {summary.old_regime.chapter_via_deductions:,.2f}",
        f"INR {summary.new_regime.chapter_via_deductions:,.2f}",
    ])
    writer.writerow([
        "Taxable Income",
        f"INR {summary.old_regime.taxable_income:,.2f}",
        f"INR {summary.new_regime.taxable_income:,.2f}",
    ])
    writer.writerow([
        "Tax on Slabs",
        f"INR {summary.old_regime.tax_on_slabs:,.2f}",
        f"INR {summary.new_regime.tax_on_slabs:,.2f}",
    ])
    writer.writerow([
        "Sec 87A Rebate",
        f"INR {summary.old_regime.section_87a_rebate:,.2f}",
        f"INR {summary.new_regime.section_87a_rebate:,.2f}",
    ])
    writer.writerow([
        "Health & Edu Cess (4%)",
        f"INR {summary.old_regime.cess:,.2f}",
        f"INR {summary.new_regime.cess:,.2f}",
    ])
    writer.writerow([
        "Total Tax Liability",
        f"INR {summary.old_regime.total_tax_liability:,.2f}",
        f"INR {summary.new_regime.total_tax_liability:,.2f}",
    ])
    writer.writerow([
        "TDS Credits",
        f"INR {summary.old_regime.tds_credits:,.2f}",
        f"INR {summary.new_regime.tds_credits:,.2f}",
    ])
    writer.writerow([
        "Net Tax Payable",
        f"INR {summary.old_regime.net_tax_payable:,.2f}",
        f"INR {summary.new_regime.net_tax_payable:,.2f}",
    ])

    filename = f"tax_summary_{summary.financial_year}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/pdf")
def export_tax_summary_pdf(
    financial_year: str = Query(
        "2024-25", description="Financial Year (e.g. '2024-25')"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Export Tax Readiness Summary Report as PDF with mandatory legal disclaimer.
    """
    summary = TaxRegimeService.compute_tax_summary(
        db, user_id=current_user.id, financial_year=financial_year
    )
    tot_gross_inc = summary.income_summary.total_gross_income

    if not REPORTLAB_AVAILABLE:
        # Fallback text PDF content
        text_content = (
            f"=== ArthSaarthi - Tax Summary ({summary.financial_year}) ===\n"
            f"RECOMMENDED REGIME: {summary.recommended_regime}\n\n"
            f"{MANDATORY_TAX_DISCLAIMER}\n\n"
            f"Total Gross Income: INR {tot_gross_inc:,.2f}\n"
            f"Old Tax Liability: INR {summary.old_regime.total_tax_liability:,.2f}\n"
            f"New Tax Liability: INR {summary.new_regime.total_tax_liability:,.2f}\n"
        )
        pdf_bytes = (
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 << /Type /Font "
            b"/Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n"
            b"4 0 obj\n<< /Length 200 >>\nstream\nBT /F1 12 Tf 50 700 Td ("
            + text_content[:150].encode('latin-1', errors='ignore')
            + b") Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n"
            b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
            b"0000000260 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\n"
            b"startxref\n510\n%%EOF"
        )
        disp_header = f"attachment; filename=tax_summary_{summary.financial_year}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": disp_header},
        )

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 40, "ArthSaarthi - Tax Readiness Summary Report")
    p.setFont("Helvetica", 10)
    subtitle = (
        f"Financial Year: {summary.financial_year} | "
        f"Recommended: {summary.recommended_regime} Regime"
    )
    p.drawString(50, height - 55, subtitle)

    # Legal Warning Box
    p.setStrokeColorRGB(0.8, 0.2, 0.2)
    p.setFillColorRGB(0.98, 0.95, 0.95)
    p.rect(45, height - 120, width - 90, 55, fill=1)

    p.setFillColorRGB(0.7, 0.1, 0.1)
    p.setFont("Helvetica-Bold", 8)
    p.drawString(55, height - 75, "IMPORTANT LEGAL NOTICE & TAX DISCLAIMER")
    p.setFont("Helvetica", 7)
    p.drawString(
        55,
        height - 87,
        "This report is for informational & tax planning purposes ONLY.",
    )
    p.drawString(
        55,
        height - 97,
        "Calculations do NOT represent final official liabilities. "
        "Neither ArthSaarthi nor its developers accept liability.",
    )
    p.drawString(
        55,
        height - 107,
        "For actual calculation and ITR filing, users MUST consult a CA.",
    )

    # Financial Details
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, height - 140, "1. Income & Deductions Summary")
    p.setFont("Helvetica", 9)
    inc_str = f"Total Gross Income: INR {tot_gross_inc:,.2f}"
    p.drawString(50, height - 155, inc_str)
    ded_str = (
        f"Total Chapter VI-A Deductions: INR "
        f"{summary.deduction_summary.total_chapter_via_deductions:,.2f}"
    )
    p.drawString(50, height - 170, ded_str)
    tds_str = f"Total TDS Credits: INR {summary.income_summary.total_tds_credits:,.2f}"
    p.drawString(50, height - 185, tds_str)

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, height - 215, "2. Dual Regime Comparison (Old vs New)")

    p.setFont("Helvetica-Bold", 9)
    p.drawString(50, height - 235, "Metric")
    p.drawString(250, height - 235, "Old Tax Regime")
    p.drawString(400, height - 235, "New Tax Regime (115BAC)")

    p.setFont("Helvetica", 9)
    old_r = summary.old_regime
    new_r = summary.new_regime
    metrics = [
        ("Gross Income", old_r.gross_income, new_r.gross_income),
        ("Standard Deduction", old_r.exemptions, new_r.exemptions),
        (
            "Chapter VI-A Deductions",
            old_r.chapter_via_deductions,
            new_r.chapter_via_deductions,
        ),
        ("Taxable Income", old_r.taxable_income, new_r.taxable_income),
        ("Tax on Slabs", old_r.tax_on_slabs, new_r.tax_on_slabs),
        ("Sec 87A Rebate", old_r.section_87a_rebate, new_r.section_87a_rebate),
        ("Health & Edu Cess (4%)", old_r.cess, new_r.cess),
        (
            "Total Tax Liability",
            old_r.total_tax_liability,
            new_r.total_tax_liability,
        ),
        ("TDS Credits", old_r.tds_credits, new_r.tds_credits),
        ("Net Tax Payable", old_r.net_tax_payable, new_r.net_tax_payable),
    ]

    y_pos = height - 250
    for label, old_val, new_val in metrics:
        p.drawString(50, y_pos, label)
        p.drawString(250, y_pos, f"INR {old_val:,.2f}")
        p.drawString(400, y_pos, f"INR {new_val:,.2f}")
        y_pos -= 15

    # Footer Disclaimer
    p.setFont("Helvetica-Oblique", 7)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    footer_text = (
        "ArthSaarthi Legal Notice: Generated for planning purposes only. "
        "Consult a Chartered Accountant for ITR filing."
    )
    p.drawString(50, 30, footer_text)

    p.showPage()
    p.save()

    buffer.seek(0)
    filename = f"tax_summary_{summary.financial_year}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
