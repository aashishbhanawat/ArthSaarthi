from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core import security
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.enums import TransactionType
from app.services.unrealized_tax_service import UnrealizedTaxService


def create_test_user(db: Session, password: str = "TestPassword123!") -> User:
    user = User(
        email="test_tax_user@example.com",
        hashed_password=security.get_password_hash(password),
        full_name="Tax Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_unrealized_tax_service_no_holdings(db: Session):
    user = create_test_user(db)
    service = UnrealizedTaxService(db)
    summary = service.calculate_unrealized_gains(
        user_id=str(user.id),
        fy_year="2025-26",
    )
    assert summary.financial_year == "2025-26"
    assert summary.total_unrealized_stcg == Decimal("0.0")
    assert summary.total_unrealized_ltcg == Decimal("0.0")
    assert summary.section_112a_remaining_headroom == Decimal("125000.00")
    assert len(summary.lots) == 0


def test_unrealized_tax_service_with_equity_lots(db: Session):
    user = create_test_user(db)
    # Setup Portfolio & Asset
    portfolio = Portfolio(
        user_id=user.id,
        name="Test Tax Portfolio",
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    asset = Asset(
        name="Test Reliance Equity",
        ticker_symbol="RELIANCE",
        asset_type="STOCKS",
        currency="INR",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Add Buy Transaction from 400 days ago (LTCG)
    tx_date = date.today() - timedelta(days=400)
    tx = Transaction(
        user_id=user.id,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_type=TransactionType.BUY,
        transaction_date=tx_date,
        quantity=Decimal("10"),
        price_per_unit=Decimal("2000.00"),
    )
    db.add(tx)
    db.commit()

    service = UnrealizedTaxService(db)
    summary = service.calculate_unrealized_gains(
        user_id=str(user.id),
        fy_year="2025-26",
    )

    assert summary.total_unrealized_ltcg == Decimal("5500.00")  # (2550-2000)*10
    assert summary.section_112a_unrealized_eligible == Decimal("5500.00")
    assert summary.section_112a_unrealized_exemption_used == Decimal("5500.00")
    assert summary.estimated_unrealized_ltcg_tax == Decimal("0.0")
    assert len(summary.lots) == 1
    assert summary.lots[0].gain_type == "LTCG"
    assert summary.lots[0].holding_days >= 400


def test_unrealized_gains_api_endpoint(client: TestClient, db: Session, get_auth_headers):
    password = "TestPassword123!"
    user = create_test_user(db, password)
    headers = get_auth_headers(user.email, password)
    response = client.get(
        "/api/v1/capital-gains/unrealized?fy=2025-26",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_unrealized_stcg" in data
    assert "total_unrealized_ltcg" in data
    assert "section_112a_remaining_headroom" in data
    assert "lots" in data
