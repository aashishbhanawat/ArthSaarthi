from datetime import date, datetime, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core import security
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.transaction_link import TransactionLink
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


def test_realized_ltcg_reduces_112a_headroom(db: Session):
    user = create_test_user(db)
    portfolio = Portfolio(user_id=user.id, name="Realized Test Portfolio")
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    asset = Asset(
        name="Nitin Spinners Ltd",
        ticker_symbol="NITINSPIN",
        asset_type="STOCKS",
        currency="INR",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Buy 300 @ 200 on 31 Oct 2022
    buy_tx = Transaction(
        user_id=user.id,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_type=TransactionType.BUY,
        transaction_date=datetime(2022, 10, 31),
        quantity=Decimal("300"),
        price_per_unit=Decimal("200.00"),
    )
    db.add(buy_tx)
    db.commit()
    db.refresh(buy_tx)

    # Sell 150 @ 560 on 01 May 2026 (FY 2026-27) -> LTCG = (560-200)*150 = 54000
    sell_tx = Transaction(
        user_id=user.id,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        transaction_type=TransactionType.SELL,
        transaction_date=datetime(2026, 5, 1),
        quantity=Decimal("150"),
        price_per_unit=Decimal("560.00"),
    )
    db.add(sell_tx)
    db.commit()
    db.refresh(sell_tx)

    link = TransactionLink(
        buy_transaction_id=buy_tx.id,
        sell_transaction_id=sell_tx.id,
        quantity=Decimal("150"),
    )
    db.add(link)
    db.commit()

    service = UnrealizedTaxService(db)
    summary = service.calculate_unrealized_gains(
        user_id=str(user.id),
        fy_year="2026-27",
    )

    # Realized LTCG = 54,000
    assert summary.section_112a_realized_used == Decimal("54000.00")
    # Remaining headroom = 125,000 - 54,000 = 71,000
    assert summary.section_112a_remaining_headroom == Decimal("71000.00")


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
