from datetime import date
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_tax_deduction_crud_and_summary_capping(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # 1. Create 80C deduction exceeding ₹1.5L statutory cap (e.g. ₹2,00,000)
    entry_80c = {
        "financial_year": "2025-2026",
        "section": "80C",
        "title": "LIC Premium & ELSS Funds",
        "amount": 200000.0,
        "deduction_date": date.today().isoformat(),
        "proof_notes": "Policy #123456",
    }
    res = client.post(
        f"{settings.API_V1_STR}/tax/deductions",
        json=entry_80c,
        headers=headers,
    )
    assert res.status_code == 201
    created_80c = res.json()
    assert created_80c["financial_year"] == "2025-2026"
    assert created_80c["section"] == "80C"
    assert float(created_80c["amount"]) == 200000.0
    deduction_id = created_80c["id"]

    # 2. Create 80D health insurance deduction exceeding ₹25k cap (e.g. ₹30,000)
    entry_80d = {
        "financial_year": "2025-2026",
        "section": "80D",
        "title": "Star Health Premium",
        "amount": 30000.0,
        "deduction_date": date.today().isoformat(),
        "proof_notes": "Receipt #9876",
    }
    res_80d = client.post(
        f"{settings.API_V1_STR}/tax/deductions",
        json=entry_80d,
        headers=headers,
    )
    assert res_80d.status_code == 201

    # 3. Read list of deductions
    res_list = client.get(
        f"{settings.API_V1_STR}/tax/deductions?financial_year=2025-2026",
        headers=headers,
    )
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 2

    # 4. Get FY Summary and verify statutory capping calculation
    res_sum = client.get(
        f"{settings.API_V1_STR}/tax/deductions/summary?financial_year=2025-2026",
        headers=headers,
    )
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["financial_year"] == "2025-2026"
    assert float(summary["total_invested"]) == 230000.0
    # Capping: 80C capped at 150000 + 80D capped at 25000 = 175000
    assert float(summary["total_eligible_deduction"]) == 175000.0

    # Verify section limits inside summary
    sec_80c_summary = next(
        (s for s in summary["sections"] if s["section"] == "80C"), None
    )
    assert sec_80c_summary is not None
    assert float(sec_80c_summary["total_invested"]) == 200000.0
    assert float(sec_80c_summary["max_limit"]) == 150000.0
    assert float(sec_80c_summary["eligible_deduction"]) == 150000.0

    sec_80d_summary = next(
        (s for s in summary["sections"] if s["section"] == "80D"), None
    )
    assert sec_80d_summary is not None
    assert float(sec_80d_summary["total_invested"]) == 30000.0
    assert float(sec_80d_summary["max_limit"]) == 25000.0
    assert float(sec_80d_summary["eligible_deduction"]) == 25000.0

    # 5. Update entry
    update_data = {
        "amount": 140000.0,
        "title": "Updated LIC Premium",
    }
    res_up = client.put(
        f"{settings.API_V1_STR}/tax/deductions/{deduction_id}",
        json=update_data,
        headers=headers,
    )
    assert res_up.status_code == 200
    assert float(res_up.json()["amount"]) == 140000.0
    assert res_up.json()["title"] == "Updated LIC Premium"

    # 6. Delete entry
    res_del = client.delete(
        f"{settings.API_V1_STR}/tax/deductions/{deduction_id}",
        headers=headers,
    )
    assert res_del.status_code == 200


def test_tax_deduction_tenant_isolation(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user_a, password_a = create_random_user(db)
    headers_a = get_auth_headers(user_a.email, password_a)

    user_b, password_b = create_random_user(db)
    headers_b = get_auth_headers(user_b.email, password_b)

    # User A creates entry
    res_a = client.post(
        f"{settings.API_V1_STR}/tax/deductions",
        json={
            "financial_year": "2025-2026",
            "section": "80C",
            "title": "User A PPF",
            "amount": 50000.0,
            "deduction_date": date.today().isoformat(),
        },
        headers=headers_a,
    )
    entry_a_id = res_a.json()["id"]

    # User B should NOT see User A's deduction entry
    res_b_list = client.get(
        f"{settings.API_V1_STR}/tax/deductions?financial_year=2025-2026",
        headers=headers_b,
    )
    assert res_b_list.status_code == 200
    assert len(res_b_list.json()) == 0

    # User B should NOT be able to delete User A's entry
    res_b_del = client.delete(
        f"{settings.API_V1_STR}/tax/deductions/{entry_a_id}",
        headers=headers_b,
    )
    assert res_b_del.status_code == 404
