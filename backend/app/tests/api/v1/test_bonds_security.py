from datetime import date
from decimal import Decimal
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.bond import Bond
from app.schemas.enums import BondType
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_bond_authorization(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    # Setup user A and portfolio A
    user_a, password_a = create_random_user(db)
    portfolio_a = create_test_portfolio(db, user_id=user_a.id, name="Portfolio A")
    asset = create_test_asset(db, ticker_symbol="TEST-BOND-A")
    asset.asset_type = "BOND"
    db.commit()
    create_test_transaction(
        db,
        portfolio_id=portfolio_a.id,
        ticker=asset.ticker_symbol,
        asset_id=str(asset.id)
    )

    bond = Bond(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        face_value=Decimal("1000"),
        coupon_rate=Decimal("5"),
        maturity_date=date(2030, 1, 1),
    )
    db.add(bond)
    db.commit()
    db.refresh(bond)

    # Setup user B
    user_b, password_b = create_random_user(db)
    headers_b = get_auth_headers(user_b.email, password_b)

    # Payload
    data = {
        "bond_type": "GOVERNMENT",
        "face_value": 2000,
        "coupon_rate": 6,
        "maturity_date": "2031-01-01",
        "asset_id": str(asset.id),  # Added this for validation
    }

    # User B tries to update a bond in User A's portfolio
    response = client.put(
        f"{settings.API_V1_STR}/portfolios/{portfolio_a.id}/bonds/{bond.id}",
        headers=headers_b,
        json=data,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    assert response.status_code == 403


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_read_delete_bond_authorization(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    # Setup user A and portfolio A
    user_a, password_a = create_random_user(db)
    portfolio_a = create_test_portfolio(db, user_id=user_a.id, name="Portfolio A")
    asset = create_test_asset(db, ticker_symbol="TEST-BOND-READ")
    asset.asset_type = "BOND"
    db.commit()
    create_test_transaction(
        db,
        portfolio_id=portfolio_a.id,
        ticker=asset.ticker_symbol,
        asset_id=str(asset.id)
    )

    bond = Bond(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        face_value=Decimal("1000"),
        coupon_rate=Decimal("5"),
        maturity_date=date(2030, 1, 1),
    )
    db.add(bond)
    db.commit()
    db.refresh(bond)

    # Setup user B
    user_b, password_b = create_random_user(db)
    headers_b = get_auth_headers(user_b.email, password_b)

    # User B tries to read a bond in User A's portfolio
    response_read = client.get(
        f"{settings.API_V1_STR}/portfolios/{portfolio_a.id}/bonds/{bond.id}",
        headers=headers_b,
    )
    assert response_read.status_code == 403

    # User B tries to delete a bond in User A's portfolio
    response_delete = client.delete(
        f"{settings.API_V1_STR}/portfolios/{portfolio_a.id}/bonds/{bond.id}",
        headers=headers_b,
    )
    assert response_delete.status_code == 403


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_bond_no_transactions_authorization(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    # Setup user A
    user_a, password_a = create_random_user(db)
    asset = create_test_asset(db, ticker_symbol="TEST-BOND-NO-TX")
    asset.asset_type = "BOND"
    db.commit()

    bond = Bond(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        face_value=Decimal("1000"),
        coupon_rate=Decimal("5"),
        maturity_date=date(2030, 1, 1),
    )
    db.add(bond)
    db.commit()
    db.refresh(bond)

    # Setup user B
    user_b, password_b = create_random_user(db)
    headers_b = get_auth_headers(user_b.email, password_b)

    # User B tries to read a bond that has no transactions
    response = client.get(
        f"{settings.API_V1_STR}/portfolios/{user_a.id}/bonds/{bond.id}",
        # Just dummy portfolio ID
        headers=headers_b,
    )
    assert response.status_code == 403
