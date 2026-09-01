from datetime import date
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_income_source_crud(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # 1. Create source
    data = {
        "name": "Primary Tech Salary",
        "category": "SALARY",
        "payer_name": "Acme Solutions Ltd",
    }
    res = client.post(
        f"{settings.API_V1_STR}/income/sources",
        json=data,
        headers=headers,
    )
    assert res.status_code == 201
    source = res.json()
    assert source["name"] == "Primary Tech Salary"
    assert source["category"] == "SALARY"
    assert source["payer_name"] == "Acme Solutions Ltd"
    source_id = source["id"]

    # 2. Read sources
    res_list = client.get(
        f"{settings.API_V1_STR}/income/sources",
        headers=headers,
    )
    assert res_list.status_code == 200
    sources = res_list.json()
    assert len(sources) == 1
    assert sources[0]["id"] == source_id

    # 3. Update source
    update_data = {
        "name": "Primary Tech Salary (Senior Lead)",
        "payer_name": "Acme Corp International",
    }
    res_up = client.put(
        f"{settings.API_V1_STR}/income/sources/{source_id}",
        json=update_data,
        headers=headers,
    )
    assert res_up.status_code == 200
    assert res_up.json()["name"] == "Primary Tech Salary (Senior Lead)"
    assert res_up.json()["payer_name"] == "Acme Corp International"

    # 4. Delete source
    res_del = client.delete(
        f"{settings.API_V1_STR}/income/sources/{source_id}",
        headers=headers,
    )
    assert res_del.status_code == 200

    # Verify deleted
    res_list_after = client.get(
        f"{settings.API_V1_STR}/income/sources",
        headers=headers,
    )
    assert len(res_list_after.json()) == 0


def test_income_entry_crud_and_summary(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    # Create source first
    res_src = client.post(
        f"{settings.API_V1_STR}/income/sources",
        json={
            "name": "Freelance Consulting",
            "category": "FREELANCE",
            "payer_name": "Global Tech Client",
        },
        headers=headers,
    )
    assert res_src.status_code == 201
    source_id = res_src.json()["id"]

    # 1. Create Income Entry
    entry_data = {
        "source_id": source_id,
        "financial_year": "2025-2026",
        "entry_date": date.today().isoformat(),
        "gross_amount": 150000.0,
        "tds_amount": 15000.0,
        "notes": "Q1 Retainer Fee",
    }
    res_e = client.post(
        f"{settings.API_V1_STR}/income/entries",
        json=entry_data,
        headers=headers,
    )
    assert res_e.status_code == 201
    entry = res_e.json()
    assert entry["financial_year"] == "2025-2026"
    assert float(entry["gross_amount"]) == 150000.0
    assert float(entry["tds_amount"]) == 15000.0
    assert float(entry["net_amount"]) == 135000.0
    assert entry["source_name"] == "Freelance Consulting"
    entry_id = entry["id"]

    # 2. Create second entry for same source
    client.post(
        f"{settings.API_V1_STR}/income/entries",
        json={
            "source_id": source_id,
            "financial_year": "2025-2026",
            "entry_date": date.today().isoformat(),
            "gross_amount": 100000.0,
            "tds_amount": 10000.0,
            "notes": "Q2 Retainer Fee",
        },
        headers=headers,
    )

    # 3. Read entries
    res_read = client.get(
        f"{settings.API_V1_STR}/income/entries?financial_year=2025-2026",
        headers=headers,
    )
    assert res_read.status_code == 200
    entries = res_read.json()
    assert len(entries) == 2

    # 4. Get FY Summary
    res_sum = client.get(
        f"{settings.API_V1_STR}/income/summary?financial_year=2025-2026",
        headers=headers,
    )
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["financial_year"] == "2025-2026"
    assert float(summary["total_gross"]) == 250000.0
    assert float(summary["total_tds"]) == 25000.0
    assert float(summary["total_net"]) == 225000.0
    assert len(summary["source_breakdown"]) == 1

    # 5. Delete entry
    res_del = client.delete(
        f"{settings.API_V1_STR}/income/entries/{entry_id}",
        headers=headers,
    )
    assert res_del.status_code == 200


def test_income_entry_tds_validation(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    res_src = client.post(
        f"{settings.API_V1_STR}/income/sources",
        json={"name": "Rental Income", "category": "RENTAL"},
        headers=headers,
    )
    source_id = res_src.json()["id"]

    # TDS > Gross should fail with 422 Unprocessable Entity
    invalid_data = {
        "source_id": source_id,
        "financial_year": "2025-2026",
        "entry_date": date.today().isoformat(),
        "gross_amount": 50000.0,
        "tds_amount": 60000.0,  # Invalid
    }
    res = client.post(
        f"{settings.API_V1_STR}/income/entries",
        json=invalid_data,
        headers=headers,
    )
    assert res.status_code == 422


def test_income_tenant_isolation(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user_a, password_a = create_random_user(db)
    headers_a = get_auth_headers(user_a.email, password_a)

    user_b, password_b = create_random_user(db)
    headers_b = get_auth_headers(user_b.email, password_b)

    # User A creates source
    res_a = client.post(
        f"{settings.API_V1_STR}/income/sources",
        json={"name": "User A Salary", "category": "SALARY"},
        headers=headers_a,
    )
    source_a_id = res_a.json()["id"]

    # User B should NOT see User A's source
    res_b_list = client.get(
        f"{settings.API_V1_STR}/income/sources",
        headers=headers_b,
    )
    assert res_b_list.status_code == 200
    assert len(res_b_list.json()) == 0

    # User B should NOT be able to delete or update User A's source (returns 404)
    res_b_del = client.delete(
        f"{settings.API_V1_STR}/income/sources/{source_a_id}",
        headers=headers_b,
    )
    assert res_b_del.status_code == 404

    # User B cannot create an entry linking to User A's source (returns 400)
    res_b_entry = client.post(
        f"{settings.API_V1_STR}/income/entries",
        json={
            "source_id": source_a_id,
            "financial_year": "2025-2026",
            "entry_date": date.today().isoformat(),
            "gross_amount": 50000.0,
            "tds_amount": 5000.0,
        },
        headers=headers_b,
    )
    assert res_b_entry.status_code == 400


def test_income_entry_salary_breakdown_and_hra_exemption(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    res_src = client.post(
        f"{settings.API_V1_STR}/income/sources",
        json={
            "name": "Primary Salary Source",
            "category": "SALARY",
            "payer_name": "Tech Corp",
        },
        headers=headers,
    )
    assert res_src.status_code == 201
    source_id = res_src.json()["id"]

    # Log income entry with salary components
    # (Basic, HRA, DA, Special, Other Allowances, Benefits, Rent Paid, Metro)
    entry_payload = {
        "source_id": source_id,
        "financial_year": "2026-2027",
        "entry_date": date.today().isoformat(),
        "gross_amount": 100000.0,
        "tds_amount": 10000.0,
        "basic_amount": 50000.0,
        "hra_amount": 25000.0,
        "da_amount": 0.0,
        "special_allowance_amount": 15000.0,
        "other_allowances_amount": 5000.0,
        "other_benefits_amount": 5000.0,
        "rent_paid": 20000.0,
        "is_metro": True,
        "notes": "May 2026 Monthly Salary with HRA Exemption",
    }
    res = client.post(
        f"{settings.API_V1_STR}/income/entries",
        json=entry_payload,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()

    assert data["source_id"] == source_id
    assert float(data["gross_amount"]) == 100000.0
    assert float(data["basic_amount"]) == 50000.0
    assert float(data["hra_amount"]) == 25000.0
    assert float(data["special_allowance_amount"]) == 15000.0
    assert float(data["other_allowances_amount"]) == 5000.0
    assert float(data["other_benefits_amount"]) == 5000.0
    assert float(data["rent_paid"]) == 20000.0
    assert data["is_metro"] is True

    # Check HRA Exemption math:
    # Basic + DA = 50,000
    # Opt 1: Actual HRA = 25,000
    # Opt 2: Rent Paid - 10% Basic = 20,000 - 5,000 = 15,000
    # Opt 3: 50% Basic (Metro) = 25,000
    # Minimum = 15,000
    assert float(data["hra_exemption"]) == 15000.0

