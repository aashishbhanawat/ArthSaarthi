from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app import crud, schemas
from app.crud.crud_analytics import analytics
from app.crud.crud_dashboard import dashboard
from app.crud.crud_holding import holding
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.user import User

# --- Mock Data ---
MOCK_FX_RATE = Decimal("85.0")
MOCK_USD_PRICE = Decimal("100.0")


@pytest.fixture
def mock_financial_data_service():
    with patch("app.crud.crud_dashboard.financial_data_service") as mock_service:
        # Mock get_historical_prices to return data for both the stock and FX
        mock_service.get_historical_prices.side_effect = (
            lambda assets, start_date, end_date: {
                "GOOGL": {
                    d: MOCK_USD_PRICE
                    for d in [
                        start_date + timedelta(days=i)
                        for i in range((end_date - start_date).days + 1)
                    ]
                },
                "USDINR=X": {
                    d: MOCK_FX_RATE
                    for d in [
                        start_date + timedelta(days=i)
                        for i in range((end_date - start_date).days + 1)
                    ]
                },
            }
        )
        yield mock_service


@pytest.fixture
def foreign_asset(db: Session) -> Asset:
    asset = Asset(
        ticker_symbol="GOOGL",
        name="Alphabet Inc.",
        asset_type="STOCK",
        currency="USD",
        exchange="NASDAQ",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@pytest.fixture
def test_user_portfolio(db: Session) -> tuple[User, Portfolio]:
    # Use a strong password to satisfy validation
    user = crud.user.create(
        db,
        obj_in=schemas.UserCreate(
            email="test_foreign@example.com",
            password="Password1!",
            full_name="Foreign Tester",
        ),
    )
    portfolio = crud.portfolio.create_with_owner(
        db=db,
        obj_in=schemas.PortfolioCreate(name="Foreign Portfolio"),
        user_id=user.id,
    )
    return user, portfolio


def test_dashboard_history_with_foreign_asset(
    db: Session,
    test_user_portfolio,
    foreign_asset,
    mock_financial_data_service,
):
    user, portfolio = test_user_portfolio

    # 1. Create a BUY transaction for a foreign asset
    crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=foreign_asset.id,
            transaction_type="BUY",
            quantity=Decimal("10"),
            price_per_unit=MOCK_USD_PRICE,  # USD Price
            transaction_date=date.today() - timedelta(days=5),
            details={"fx_rate": float(MOCK_FX_RATE)},
        ),
        portfolio_id=portfolio.id,
    )

    # 2. Get Dashboard History
    # We expect the value to be Quantity * USD Price * FX Rate
    history = dashboard.get_history(db=db, user=user, range_str="7d")

    assert len(history) > 0
    latest_point = history[-1]

    expected_value_inr = 10 * MOCK_USD_PRICE * MOCK_FX_RATE
    assert latest_point["value"] == expected_value_inr


def test_analytics_xirr_with_rsu_vest(
    db: Session, test_user_portfolio, foreign_asset
):
    user, portfolio = test_user_portfolio

    # 1. Create an RSU VEST transaction
    # FMV: $100, Qty: 10, FX: 85 -> Value INR: 85,000
    # This acts as an outflow in XIRR
    vest_date = date.today() - timedelta(days=365)
    crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=foreign_asset.id,
            transaction_type="RSU_VEST",
            quantity=Decimal("10"),
            price_per_unit=Decimal("0"),  # Price is 0 for vest
            transaction_date=vest_date,
            details={"fmv": 100.0, "fx_rate": 85.0},
        ),
        portfolio_id=portfolio.id,
    )

    # 2. Simulate current price update (via holding calculation or mock)
    # Since we can't easily mock the holding calculation's internal price fetch here
    # without more complex mocking, we'll rely on the fact that crud_holding calculates
    # current_value. However, for this test, we want to verify the cash flow logic
    # in analytics.

    # We need a current price for the holding to have a positive XIRR.
    # We can mock `crud.holding.get_portfolio_holdings_and_summary`

    with patch(
        "app.crud.crud_analytics.crud.holding.get_portfolio_holdings_and_summary"
    ) as mock_holdings:
        mock_holdings.return_value = schemas.PortfolioHoldingsAndSummary(
            summary=schemas.PortfolioSummary(
                total_value=Decimal("90000"),  # Appreciation
                total_invested_amount=Decimal("85000"),
                days_pnl=Decimal("0"),
                total_unrealized_pnl=Decimal("5000"),
                total_realized_pnl=Decimal("0"),
            ),
            holdings=[
                schemas.Holding(
                    asset_id=foreign_asset.id,
                    ticker_symbol="GOOGL",
                    asset_name="Google",
                    asset_type="STOCK",
                    quantity=Decimal("10"),
                    average_buy_price=Decimal("0"),  # Irrelevant for this check
                    total_invested_amount=Decimal("85000"),
                    current_price=Decimal("9000"),  # 9000 INR per unit (~$105)
                    current_value=Decimal("90000"),
                    currency="USD",
                    group="EQUITIES",
                    days_pnl=Decimal("0"),
                    days_pnl_percentage=0.0,
                    unrealized_pnl=Decimal("5000"),
                    realized_pnl=Decimal("0"),
                    unrealized_pnl_percentage=0.0,
                )
            ],
        )

        # We also need to mock `crud.transaction.get_multi_by_portfolio`
        # to return our RSU vest.
        # Actually, the real DB call works fine, we just inserted it.

        stats = analytics.get_portfolio_analytics(db=db, portfolio_id=portfolio.id)

        # Input: -85,000 (1 yr ago)
        # Current: +90,000
        # Gain: ~5.8%

        assert stats.xirr > 0.05
        assert stats.xirr < 0.06


def test_get_holdings_current_value_conversion(
    db: Session, test_user_portfolio, foreign_asset
):
    """
    Verifies that `get_portfolio_holdings_and_summary` fetches the current FX rate
    and converts the foreign asset's current value to INR.
    """
    user, portfolio = test_user_portfolio

    # 1. Create a BUY transaction
    # Price: $100, Qty: 10, FX: 85 -> Invested: 85,000 INR
    crud.transaction.create_with_portfolio(
        db=db,
        obj_in=schemas.TransactionCreate(
            asset_id=foreign_asset.id,
            transaction_type="BUY",
            quantity=Decimal("10"),
            price_per_unit=MOCK_USD_PRICE,
            transaction_date=date.today() - timedelta(days=10),
            details={"fx_rate": float(MOCK_FX_RATE)},
        ),
        portfolio_id=portfolio.id,
    )

    # 2. Mock `financial_data_service.get_current_prices`
    # We need to return BOTH the asset price (USD) and the FX rate (INR).
    # Let's say current price is $110, and FX rate is 86.0.
    # Expected Current Value = 10 * 110 * 86 = 94,600 INR.

    current_usd_price = Decimal("110.0")
    current_fx_rate = Decimal("86.0")

    with patch(
        "app.crud.crud_holding.financial_data_service.get_current_prices"
    ) as mock_prices:

        def side_effect(assets):
            result = {}
            for a in assets:
                ticker = a["ticker_symbol"]
                if ticker == "GOOGL":
                    result[ticker] = {
                        "current_price": current_usd_price,
                        "previous_close": current_usd_price,
                    }
                elif ticker == "USDINR=X":
                    result[ticker] = {
                        "current_price": current_fx_rate,
                        "previous_close": current_fx_rate,
                    }
            return result

        mock_prices.side_effect = side_effect

        # 3. Call get_portfolio_holdings_and_summary
        holdings_data = holding.get_portfolio_holdings_and_summary(
            db=db, portfolio_id=portfolio.id
        )

        assert len(holdings_data.holdings) == 1
        h = holdings_data.holdings[0]

        # Verify Total Invested (uses historical FX rate 85.0)
        # 10 * 100 * 85 = 85,000
        assert h.total_invested_amount == Decimal(
            "85000.00"
        ) or h.total_invested_amount == Decimal("85000")

        # Verify Current Value (uses current FX rate 86.0)
        # 10 * 110 * 86 = 94,600
        expected_current_value = Decimal("10") * current_usd_price * current_fx_rate
        assert h.current_value == expected_current_value

        # Verify Unrealized PnL
        # 94,600 - 85,000 = 9,600
        assert h.unrealized_pnl == expected_current_value - Decimal("85000")
