import uuid
from datetime import date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas.asset import AssetCreate
from app.schemas.transaction import TransactionCreate
from app.tests.utils.user import create_random_user, get_access_token
from app.tests.utils.portfolio import create_test_portfolio

def test_ppf_interest_calculation(client: TestClient, db: Session) -> None:
    # 1. Create user and portfolio
    user, password = create_random_user(db)
    token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {token}"}
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")

    # 2. Create a PPF Asset
    ppf_asset_in = AssetCreate(
        ticker_symbol="PPF_TEST_ACCOUNT",
        name="Test PPF Account",
        asset_type="PPF",
        currency="INR",
        account_number="123456789",
        opening_date=date(2020, 1, 15),
    )
    ppf_asset = crud.asset.create(db, obj_in=ppf_asset_in)

    # 3. Add some contributions
    contributions = [
        {"date": date(2020, 2, 10), "amount": Decimal("50000")},
        {"date": date(2021, 5, 20), "amount": Decimal("60000")},
        {"date": date(2022, 12, 1), "amount": Decimal("40000")},
    ]
    for c in contributions:
        tx_in = TransactionCreate(
            asset_id=ppf_asset.id,
            transaction_type="CONTRIBUTION",
            quantity=1,
            price_per_unit=c["amount"],
            transaction_date=datetime.combine(c["date"], datetime.min.time()),
            fees=0,
        )
        crud.transaction.create_with_portfolio(db, obj_in=tx_in, portfolio_id=portfolio.id)

    db.commit()

    # 4. Trigger holding calculation
    response = client.get(f"{settings.API_V1_STR}/portfolios/{portfolio.id}/holdings", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # 5. Assertions
    ppf_holding = next((h for h in data["holdings"] if h["asset_type"] == "PPF"), None)
    assert ppf_holding is not None

    total_contributions = sum(c["amount"] for c in contributions)
    assert Decimal(ppf_holding["total_invested_amount"]) == total_contributions
    assert Decimal(ppf_holding["unrealized_pnl"]) > 0
    assert Decimal(ppf_holding["current_value"]) > total_contributions

def test_admin_can_manage_interest_rates(client: TestClient, db: Session) -> None:
    # 1. Create admin user
    admin, password = create_random_user(db, is_admin=True)
    token = get_access_token(client, admin.email, password)
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a new interest rate
    rate_in = {
        "scheme_name": "TEST_SCHEME",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "rate": 5.5,
    }
    response = client.post(f"{settings.API_V1_STR}/admin/interest-rates/", headers=headers, json=rate_in)
    assert response.status_code == 201
    data = response.json()
    rate_id = data["id"]
    assert data["scheme_name"] == "TEST_SCHEME"
    assert float(data["rate"]) == 5.5

    # 3. Read interest rates
    response = client.get(f"{settings.API_V1_STR}/admin/interest-rates/", headers=headers)
    assert response.status_code == 200
    assert any(r["id"] == rate_id for r in response.json())

    # 4. Update the interest rate
    update_data = {"rate": 6.0}
    response = client.put(f"{settings.API_V1_STR}/admin/interest-rates/{rate_id}", headers=headers, json=update_data)
    assert response.status_code == 200
    assert float(response.json()["rate"]) == 6.0

    # 5. Delete the interest rate
    response = client.delete(f"{settings.API_V1_STR}/admin/interest-rates/{rate_id}", headers=headers)
    assert response.status_code == 200
    db.commit()

    # 6. Verify deletion
    response = client.get(f"{settings.API_V1_STR}/admin/interest-rates/", headers=headers)
    assert response.status_code == 200
    assert not any(r["id"] == rate_id for r in response.json())
