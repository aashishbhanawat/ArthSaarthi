from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.services.snapshot_service import take_snapshot_for_portfolio
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user


def test_take_snapshot_for_portfolio(db: Session, mocker):
    mocker.patch(
        "app.core.key_manager.KeyManager.is_key_loaded",
        new_callable=mocker.PropertyMock,
        return_value=True,
    )
    mocker.patch(
        "app.core.key_manager.KeyManager.master_key",
        new_callable=mocker.PropertyMock,
        return_value=b"12345678901234567890123456789012",
    )
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(db, user_id=user.id, name="Snapshot Test")

    # Mock the get_portfolio_holdings_and_summary function
    import uuid

    from app.schemas.holding import (
        Holding,
        PortfolioHoldingsAndSummary,
        PortfolioSummary,
    )

    mock_summary = PortfolioSummary(
        total_value=Decimal("5000.00"),
        total_invested_amount=Decimal("4000.00"),
        days_pnl=Decimal("10.00"),
        total_unrealized_pnl=Decimal("1000.00"),
        total_realized_pnl=Decimal("0.00")
    )
    mock_holdings = [
        Holding(
            asset_id=uuid.uuid4(),
            ticker_symbol="AAPL",
            asset_name="Apple Inc",
            asset_type="STOCK",
            currency="USD",
            group="EQUITY",
            quantity=Decimal("10"),
            average_buy_price=Decimal("100.00"),
            total_invested_amount=Decimal("1000.00"),
            current_price=Decimal("150.00"),
            current_value=Decimal("1500.00"),
            days_pnl=Decimal("0.00"),
            days_pnl_percentage=0.0,
            unrealized_pnl=Decimal("500.00"),
            unrealized_pnl_percentage=0.5
        ),
        Holding(
            asset_id=uuid.uuid4(),
            ticker_symbol="FD1",
            asset_name="FD 1",
            asset_type="FIXED_DEPOSIT",
            currency="INR",
            group="DEPOSITS",
            quantity=Decimal("1"),
            average_buy_price=Decimal("3500.00"),
            total_invested_amount=Decimal("3500.00"),
            current_price=Decimal("3500.00"),
            current_value=Decimal("3500.00"),
            days_pnl=Decimal("0.00"),
            days_pnl_percentage=0.0,
            unrealized_pnl=Decimal("0.00"),
            unrealized_pnl_percentage=0.0
        )
    ]

    mock_data = PortfolioHoldingsAndSummary(
        summary=mock_summary, holdings=mock_holdings
    )
    mocker.patch(
        "app.crud.holding.get_portfolio_holdings_and_summary", return_value=mock_data
    )

    target_date = date.today()
    snapshot = take_snapshot_for_portfolio(
        db, portfolio_id=portfolio.id, target_date=target_date
    )

    assert snapshot.total_value == Decimal("5000.00")
    assert snapshot.equity_value == Decimal("1500.00")
    assert snapshot.fd_value == Decimal("3500.00")
    assert snapshot.mf_value == Decimal("0.00")
    assert snapshot.bond_value == Decimal("0.00")
    assert len(snapshot.holdings_snapshot) == 2
