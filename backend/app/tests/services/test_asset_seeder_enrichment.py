import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.services.asset_seeder import AssetSeeder
from app.models.asset import Asset


@pytest.fixture
def seeder(db: Session):
    return AssetSeeder(db=db, debug=True)


def test_enrich_assets_concurrently(seeder, db):
    # Create dummy assets to enrich
    assets = [
        Asset(
            ticker_symbol="AAPL",
            name="Apple",
            asset_type="STOCK",
            currency="USD",
            exchange="NASDAQ"
        ),
        Asset(
            ticker_symbol="MSFT",
            name="Microsoft",
            asset_type="STOCK",
            currency="USD",
            exchange="NASDAQ"
        ),
        Asset(
            ticker_symbol="GOOG",
            name="Google",
            asset_type="STOCK",
            currency="USD",
            exchange="NASDAQ"
        ),
    ]
    db.add_all(assets)
    db.commit()
    # Reload assets to ensure they are attached to session
    for a in assets:
        db.refresh(a)

    # Mock yfinance
    with patch("yfinance.Tickers") as mock_tickers_cls:
        mock_tickers_instance = MagicMock()
        mock_tickers_cls.return_value = mock_tickers_instance

        # Setup mock tickers behavior
        mock_ticker_objs = {}
        for asset in assets:
            mock_ticker = MagicMock()
            industry = (
                "Consumer Electronics"
                if asset.ticker_symbol == "AAPL"
                else "Software"
            )
            mock_ticker.info = {
                "sector": "Technology",
                "industry": industry,
                "country": "United States",
                "marketCap": 1000000000
            }
            # For NASDAQ assets, yf_ticker is same as ticker_symbol in current logic
            mock_ticker_objs[asset.ticker_symbol] = mock_ticker

        mock_tickers_instance.tickers = mock_ticker_objs

        # Run enrich_assets
        # We need to make sure yfinance is imported successfully inside the method
        stats = seeder.enrich_assets(max_assets=10)

        # Assertions
        assert stats["enriched"] == 3
        assert stats["errors"] == 0

        # Verify db updates
        aapl = db.query(Asset).filter_by(ticker_symbol="AAPL").first()
        assert aapl.sector == "Technology"
        assert aapl.industry == "Consumer Electronics"

        msft = db.query(Asset).filter_by(ticker_symbol="MSFT").first()
        assert msft.industry == "Software"
