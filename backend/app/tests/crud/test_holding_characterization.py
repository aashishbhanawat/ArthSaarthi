from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.portfolio import Portfolio
from app.schemas.asset import AssetType
from app.schemas.transaction import TransactionCreate, TransactionType
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

# Mark all tests in this module to use the pre_unlocked_key_manager fixture
pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


@pytest.fixture(scope="function")
def setup_portfolio_with_assets(db: Session) -> Portfolio:
    """
    Sets up a portfolio with a stock and a mutual fund holding.
    """
    user, _ = create_random_user(db)
    portfolio = create_test_portfolio(
        db, user_id=user.id, name="Characterization Portfolio"
    )

    # Create a stock asset and transaction
    stock_asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="Reliance Industries",
            ticker_symbol="RELIANCE",
            asset_type=AssetType.STOCK,
            currency="INR",
            exchange="NSE",
        ),
    )
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=stock_asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_unit=Decimal("2500"),
            transaction_date=date(2023, 1, 15),
        ),
        portfolio_id=portfolio.id,
    )

    # Create a mutual fund asset and transaction
    mf_asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="Axis Bluechip Fund",
            ticker_symbol="120465",
            asset_type=AssetType.MUTUAL_FUND,
            currency="INR",
            exchange="AMFI",
        ),
    )
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=mf_asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("500"),
            price_per_unit=Decimal("45"),
            transaction_date=date(2023, 2, 20),
        ),
        portfolio_id=portfolio.id,
    )

    db.commit()
    return portfolio


def test_holding_calculation_characterization(
    db: Session, setup_portfolio_with_assets: Portfolio
):
    """
    This is a characterization test. It captures the output of the current
    holding calculation logic with a fixed set of inputs and mocked prices.
    This test should NOT be changed during the refactoring. The goal of the
    refactoring is to make the new implementation pass this exact test.
    """
    portfolio = setup_portfolio_with_assets

    # This is the fixed, predictable price data we will use.
    mock_price_data = {
        "RELIANCE": {
            "current_price": Decimal("2800.00"),
            "previous_close": Decimal("2750.00"),
        },
        "120465": {
            "current_price": Decimal("52.50"),
            "previous_close": Decimal("52.00"),
        },
    }

    with patch("app.crud.crud_holding.financial_data_service") as mock_fds:
        mock_fds.get_current_prices.return_value = mock_price_data

        result = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio.id
        )

    # --- Golden Master Assertions ---
    # These values capture the current system's behavior.
    summary = result["summary"]
    assert summary.total_value == pytest.approx(Decimal("54250.00"))
    assert summary.total_invested_amount == pytest.approx(Decimal("47500.00"))
    assert summary.days_pnl == pytest.approx(Decimal("750.00"))
    assert summary.total_unrealized_pnl == pytest.approx(Decimal("6750.00"))
    assert summary.total_realized_pnl == pytest.approx(Decimal("0.0"))
