from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.portfolio import Portfolio
from app.schemas.asset import AssetType
from app.schemas.bond import BondCreate, BondUpdate
from app.schemas.enums import BondType, PaymentFrequency
from app.schemas.transaction import TransactionCreate, TransactionType
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_lower_string


@pytest.fixture(scope="function")
def setup_portfolio_and_user(db: Session) -> Portfolio:
    user, _ = create_random_user(db)
    return create_test_portfolio(db, user_id=user.id, name="Test Portfolio")


def test_create_bond(db: Session) -> None:
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type=AssetType.BOND,
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        face_value=Decimal("1000.00"),
        coupon_rate=Decimal("7.5"),
        maturity_date=date(2030, 1, 1),
        isin="INE123456789",
        payment_frequency=PaymentFrequency.SEMI_ANNUALLY,
        first_payment_date=date(2025, 7, 1),
    )
    bond = crud.bond.create(db=db, obj_in=bond_in)
    assert bond.asset_id == asset.id
    assert bond.bond_type == "CORPORATE"
    assert bond.face_value == Decimal("1000.00")
    assert bond.coupon_rate == Decimal("7.5")
    assert bond.maturity_date == date(2030, 1, 1)


def test_get_bond(db: Session) -> None:
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type=AssetType.BOND,
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.GOVERNMENT,
        maturity_date=date(2035, 1, 1),
    )
    bond = crud.bond.create(db=db, obj_in=bond_in)
    stored_bond = crud.bond.get(db=db, id=bond.id)
    assert stored_bond
    assert stored_bond.id == bond.id
    assert stored_bond.asset_id == asset.id


def test_update_bond(db: Session) -> None:
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type=AssetType.BOND,
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        maturity_date=date(2030, 1, 1),
        coupon_rate=Decimal("8.0"),
    )
    bond = crud.bond.create(db=db, obj_in=bond_in)
    bond_update = BondUpdate(coupon_rate=Decimal("8.25"), **bond_in.model_dump(exclude={
        "coupon_rate", "asset_id"}))
    bond2 = crud.bond.update(db=db, db_obj=bond, obj_in=bond_update)
    assert bond2.id == bond.id
    assert bond2.coupon_rate == Decimal("8.25")


def test_delete_bond(db: Session) -> None:
    asset_in = schemas.AssetCreate(
        name="Test Bond Asset",
        ticker_symbol=f"BOND-{random_lower_string()}",
        asset_type=AssetType.BOND,
        currency="INR",
        exchange="NSE",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id, bond_type=BondType.TBILL, maturity_date=date(2026, 1, 1)
    )
    bond = crud.bond.create(db=db, obj_in=bond_in)
    bond2 = crud.bond.remove(db=db, id=bond.id)
    db.commit()
    bond3 = crud.bond.get(db=db, id=bond.id)
    assert bond3 is None
    assert bond2.id == bond.id


# --- Valuation Tests ---


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_tradable_bond_valuation_primary_api(
    db: Session, setup_portfolio_and_user: Portfolio
):
    """
    Tests valuation of a tradable bond using the primary (mocked) API price.
    """
    portfolio = setup_portfolio_and_user
    asset_in = schemas.AssetCreate(
        name="Test Corp Bond",
        ticker_symbol="CORPBOND",
        asset_type=AssetType.BOND,
        isin="INE001A07QF2",
        currency="INR",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        maturity_date=date(2030, 1, 1),
        face_value=1000,
        coupon_rate=7.5,
    )
    crud.bond.create(db, obj_in=bond_in)
    transaction_in = TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("50"),
        price_per_unit=Decimal("1010"),
        transaction_date=date(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio.id
    )

    with patch("app.crud.crud_holding.financial_data_service") as mock_fds:
        # Mock the batch price fetching method
        mock_fds.get_current_prices.return_value = {
            "CORPBOND": {"current_price": Decimal("1025.50"), "previous_close": Decimal(
                "1020.00")}
        }

        result = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio.id
        )
        holdings = result["holdings"]
        assert len(holdings) == 1
        bond_holding = holdings[0]
        assert bond_holding.asset_type == AssetType.BOND
        assert bond_holding.current_value == Decimal("50") * Decimal("1025.50")


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_sgb_valuation_book_value_fallback(
    db: Session, setup_portfolio_and_user: Portfolio
):
    """
    Tests SGB valuation falling back to book value when market price is unavailable.
    """
    portfolio = setup_portfolio_and_user
    asset_in = schemas.AssetCreate(
        name="SGB Test Bond",
        ticker_symbol="SGBNOV29",
        asset_type=AssetType.BOND,
        currency="INR",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id, bond_type=BondType.SGB, maturity_date=date(2029, 11, 1)
    )
    crud.bond.create(db, obj_in=bond_in)
    transaction_in = TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("10"),  # 10 grams
        price_per_unit=Decimal("5900"),
        transaction_date=date(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio.id
    )

    with patch("app.crud.crud_holding.financial_data_service") as mock_fds:
        # Mock batch price fetching to return an empty dict, simulating failure
        mock_fds.get_current_prices.return_value = {}
        # Ensure this is also mocked noqa: E501
        mock_fds.get_price_from_yfinance.return_value = None

        result = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio.id
        )
        holdings = result["holdings"]
        assert len(holdings) == 1
        sgb_holding = holdings[0]
        assert sgb_holding.asset_type == AssetType.BOND
        # With no market price and no gold price fallback, it should use book value
        assert sgb_holding.current_value == sgb_holding.total_invested_amount
        assert sgb_holding.current_value == Decimal("10") * Decimal("5900")


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_tbill_valuation_accretion_model(
    db: Session, setup_portfolio_and_user: Portfolio
):
    """
    Tests T-Bill valuation using the time-based accretion model.
    """
    portfolio = setup_portfolio_and_user
    purchase_date = date(2024, 1, 1)
    maturity_date = date(2025, 1, 1)
    valuation_date = date(2024, 7, 2)  # Approx halfway through

    asset_in = schemas.AssetCreate(
        name="91 Day T-Bill",
        ticker_symbol="TBILL91",
        asset_type=AssetType.BOND,
        currency="INR",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.TBILL,
        maturity_date=maturity_date,
        face_value=100,
    )
    crud.bond.create(db, obj_in=bond_in)
    transaction_in = TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("200"),
        price_per_unit=Decimal("97.50"),
        transaction_date=purchase_date,
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio.id
    )

    with patch("app.crud.crud_holding.financial_data_service") as mock_fds, patch(
        "app.crud.crud_holding.date"
    ) as mock_date:
        mock_fds.get_current_prices.return_value = {}  # Ensure market price fails
        mock_fds.get_price_from_yfinance.return_value = None
        mock_date.today.return_value = valuation_date

        result = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio.id
        )
        holdings = result["holdings"]
        total_days = (maturity_date - purchase_date).days
        days_elapsed = (valuation_date - purchase_date).days
        price_increase = (Decimal("100") - Decimal("97.50")) * (
            Decimal(days_elapsed) / Decimal(total_days)
        )
        expected_unit_price = Decimal("97.50") + price_increase

        assert len(holdings) == 1
        tbill_holding = holdings[0]
        assert tbill_holding.current_value == pytest.approx(
            Decimal("200") * expected_unit_price
        )


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_tradable_bond_valuation_yfinance_fallback(
    db: Session, setup_portfolio_and_user: Portfolio
):
    """
    Tests valuation of a tradable bond falling back to yfinance.
    """
    portfolio = setup_portfolio_and_user
    asset_in = schemas.AssetCreate(
        name="Test YF Bond",
        ticker_symbol="YF-BOND.NS",
        asset_type=AssetType.BOND,
        isin="INE001A07QG0",
        currency="INR",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        maturity_date=date(2030, 1, 1),
        face_value=1000,
        coupon_rate=7.5,
    )
    crud.bond.create(db, obj_in=bond_in)
    transaction_in = TransactionCreate(
        asset_id=asset.id,
        portfolio_id=portfolio.id,
        transaction_type=TransactionType.BUY,
        quantity=Decimal("20"),
        price_per_unit=Decimal("990"),
        transaction_date=date(2023, 1, 1),
    )
    crud.transaction.create_with_portfolio(
        db, obj_in=transaction_in, portfolio_id=portfolio.id
    )

    with patch("app.crud.crud_holding.financial_data_service") as mock_fds:
        # Mock the batch price fetching to fail
        mock_fds.get_current_prices.return_value = {}
        # Mock yfinance to succeed
        mock_fds.get_price_from_yfinance.return_value = Decimal("995.50")

        result = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio.id
        )
        holdings = result["holdings"]
        assert len(holdings) == 1
        bond_holding = holdings[0]
        assert bond_holding.current_value == Decimal("20") * Decimal("995.50")
        mock_fds.get_price_from_yfinance.assert_called_once_with("YF-BOND.NS")


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_bond_valuation_book_value_final_fallback(
    db: Session, setup_portfolio_and_user: Portfolio
):
    """
    Tests that a bond's value defaults to book value if all pricing methods fail.
    """
    portfolio = setup_portfolio_and_user
    asset_in = schemas.AssetCreate(
        name="Untradable Bond",
        asset_type=AssetType.BOND,
        isin=None,
        ticker_symbol="UNTRADABLE",
        currency="INR",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id, bond_type=BondType.CORPORATE, maturity_date=date(2030, 1, 1)
    )
    crud.bond.create(db, obj_in=bond_in)
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset.id,
            portfolio_id=portfolio.id,
            transaction_type=TransactionType.BUY,
            quantity=100,
            price_per_unit=950,
            transaction_date=date.today(),
        ),
        portfolio_id=portfolio.id
    )

    with patch("app.crud.crud_holding.financial_data_service") as mock_fds:
        # Mock all pricing services to fail
        mock_fds.get_current_prices.return_value = {}
        mock_fds.get_price_from_yfinance.return_value = None
        mock_fds.get_gold_price.return_value = None

        result = crud.holding.get_portfolio_holdings_and_summary(
            db, portfolio_id=portfolio.id
        )
        holdings = result["holdings"]
        assert len(holdings) == 1
        bond_holding = holdings[0]
        # Should equal invested amount (100 * 950)
        assert bond_holding.current_value == bond_holding.total_invested_amount
        assert bond_holding.total_invested_amount == Decimal("95000")


# --- Analytics Tests ---


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_bond_xirr_with_coupon_payment(
    db: Session, setup_portfolio_and_user: Portfolio
):
    """
    Tests that XIRR calculation for a bond correctly includes coupon payments.
    """
    portfolio = setup_portfolio_and_user
    asset_in = schemas.AssetCreate(
        name="Test XIRR Bond",
        ticker_symbol="XIRRBOND",
        asset_type=AssetType.BOND,
        isin="INE001A07QH8",
        currency="INR",
    )
    asset = crud.asset.create(db, obj_in=asset_in)
    bond_in = BondCreate(
        asset_id=asset.id,
        bond_type=BondType.CORPORATE,
        maturity_date=date(2030, 1, 1),
        face_value=1000,
        coupon_rate=8.0,
    )
    crud.bond.create(db, obj_in=bond_in)

    # 1. Buy transaction
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset.id,
            portfolio_id=portfolio.id,
            transaction_type=TransactionType.BUY,
            quantity=10,
            price_per_unit=1000,
            transaction_date=date(2023, 1, 1),
        ),
        portfolio_id=portfolio.id
    )
    # 2. Manual coupon transaction
    crud.transaction.create_with_portfolio(
        db,
        obj_in=TransactionCreate(
            asset_id=asset.id,
            portfolio_id=portfolio.id,
            transaction_type="COUPON",
            quantity=400,  # Represents a cash inflow of 400
            price_per_unit=1,
            transaction_date=date(2023, 7, 1),
        ),
        portfolio_id=portfolio.id
    )

    with patch("app.crud.crud_holding.financial_data_service") as mock_fds, patch("app.crud.crud_analytics.date") as mock_date:  # noqa: E501
        # Mock valuation date and price for XIRR calculation
        mock_date.today.return_value = date(2024, 1, 1)
        mock_fds.get_current_prices.return_value = {
            "XIRRBOND": {"current_price": Decimal("1050"),
                         "previous_close": Decimal("1000")}}

        analytics = crud.analytics.get_asset_analytics(
            db, asset_id=asset.id, portfolio_id=portfolio.id
        )

        print(f"Analytics being tested{analytics}")
        assert analytics is not None
        # XIRR for [-10000, 400, 10500] over 1 year is ~9.18%
        assert analytics.xirr_current == pytest.approx(0.0918, abs=1e-4)
