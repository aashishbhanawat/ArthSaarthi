from decimal import Decimal
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.tax_rules_registry import MANDATORY_TAX_DISCLAIMER, get_tax_rules
from app.crud.crud_income import crud_income_entry, crud_income_source
from app.crud.crud_tax_deduction import crud_tax_deduction
from app.schemas.income import IncomeEntryCreate, IncomeSourceCreate
from app.schemas.tax_deduction import TaxDeductionCreate
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_tax_rules_registry_multi_year():
    rules_2122 = get_tax_rules("2021-22")
    assert rules_2122.old_regime_standard_deduction == Decimal("50000")
    assert rules_2122.new_regime_standard_deduction == Decimal("0")
    assert rules_2122.section_87a_new_limit == Decimal("500000")

    rules_2324 = get_tax_rules("2023-24")
    assert rules_2324.new_regime_standard_deduction == Decimal("50000")
    assert rules_2324.section_87a_new_limit == Decimal("700000")

    rules_2425 = get_tax_rules("2024-25")
    assert rules_2425.new_regime_standard_deduction == Decimal("75000")
    assert rules_2425.section_87a_new_limit == Decimal("700000")

    rules_2627 = get_tax_rules("2026-27")
    assert rules_2627.new_regime_standard_deduction == Decimal("75000")
    assert rules_2627.section_87a_new_limit == Decimal("750000")
    assert MANDATORY_TAX_DISCLAIMER in rules_2627.disclaimer


def test_get_tax_summary_api(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # Seed Income
    source = crud_income_source.create_with_owner(
        db,
        obj_in=IncomeSourceCreate(
            name="ACME Tech Corp",
            category="SALARY",
        ),
        user_id=user.id,
    )

    crud_income_entry.create_with_owner(
        db,
        obj_in=IncomeEntryCreate(
            source_id=source.id,
            financial_year="2024-25",
            entry_date="2024-06-30",
            gross_amount=Decimal("1200000.00"),
            tds_amount=Decimal("50000.00"),
        ),
        user_id=user.id,
    )

    # Seed Tax Deduction under Section 80C
    crud_tax_deduction.create_with_owner(
        db,
        obj_in=TaxDeductionCreate(
            financial_year="2024-25",
            section="80C",
            title="PPF Deposit",
            amount=Decimal("150000.00"),
            deduction_date="2024-10-15",
        ),
        user_id=user.id,
    )

    response = client.get(
        f"{settings.API_V1_STR}/tax/summary?financial_year=2024-25",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["financial_year"] == "2024-25"
    assert "disclaimer" in data
    assert "informational, educational" in data["disclaimer"].lower()

    # Verify Gross Income & Deductions
    assert float(data["income_summary"]["gross_salary"]) == 1200000.0
    assert float(data["deduction_summary"]["section_80c"]) == 150000.0

    # Verify Dual Regime Structure
    assert data["old_regime"]["regime_type"] == "OLD"
    assert data["new_regime"]["regime_type"] == "NEW"
    assert data["recommended_regime"] in ["OLD", "NEW"]


def test_export_tax_summary_csv(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    response = client.get(
        f"{settings.API_V1_STR}/tax/summary/export/csv?financial_year=2024-25",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.content.decode("utf-8")

    # Assert mandatory disclaimer presence in CSV export
    assert "IMPORTANT LEGAL NOTICE & TAX DISCLAIMER" in content
    assert "Calculations shown do NOT represent actual final tax liabilities" in content


def test_export_tax_summary_pdf(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
):
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    response = client.get(
        f"{settings.API_V1_STR}/tax/summary/export/pdf?financial_year=2024-25",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
