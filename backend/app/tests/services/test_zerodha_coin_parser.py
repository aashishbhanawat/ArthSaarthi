"""
Unit tests for Zerodha Coin MF Parser.
"""
from pathlib import Path

import pandas as pd
import pytest

from app.services.import_parsers.zerodha_coin_parser import ZerodhaCoinParser


@pytest.fixture
def sample_zerodha_coin_df():
    """Load the sample Zerodha Coin CSV file as a DataFrame."""
    assets_dir = Path(__file__).parent.parent / "assets"
    sample_file = assets_dir / "sample_zerodha_coin.csv"

    if not sample_file.exists():
        pytest.skip(f"Sample file not found: {sample_file}")

    df = pd.read_csv(sample_file)
    return df


@pytest.fixture
def parser():
    """Create a ZerodhaCoinParser instance."""
    return ZerodhaCoinParser()


class TestZerodhaCoinParser:
    """Test suite for ZerodhaCoinParser."""

    def test_parse_returns_list_of_transactions(self, parser, sample_zerodha_coin_df):
        """Test that parse returns a non-empty list of transactions."""
        result = parser.parse(sample_zerodha_coin_df)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_correctly_classifies_buy_transactions(
        self, parser, sample_zerodha_coin_df
    ):
        """Test that buy transactions are classified as BUY."""
        result = parser.parse(sample_zerodha_coin_df)

        buy_transactions = [tx for tx in result if tx.transaction_type == "BUY"]
        assert len(buy_transactions) > 0

    def test_parse_uses_symbol_as_ticker(self, parser, sample_zerodha_coin_df):
        """Test that symbol column is used as ticker_symbol."""
        result = parser.parse(sample_zerodha_coin_df)

        for tx in result:
            assert tx.ticker_symbol is not None
            assert len(tx.ticker_symbol) > 0
            # Should contain "FUND" or "PLAN"
            assert "FUND" in tx.ticker_symbol or "PLAN" in tx.ticker_symbol

    def test_parse_preserves_date_format(self, parser, sample_zerodha_coin_df):
        """Test that dates remain in YYYY-MM-DD format."""
        result = parser.parse(sample_zerodha_coin_df)

        for tx in result:
            assert len(tx.transaction_date) == 10
            assert tx.transaction_date[4] == "-"
            assert tx.transaction_date[7] == "-"

    def test_parse_sets_zero_fees(self, parser, sample_zerodha_coin_df):
        """Test that fees are set to 0."""
        result = parser.parse(sample_zerodha_coin_df)

        for tx in result:
            assert tx.fees == 0.0

    def test_buy_sell_classification(self, parser):
        """Test buy/sell classification with mock data."""
        df = pd.DataFrame({
            "symbol": ["TEST FUND A", "TEST FUND B"],
            "trade_date": ["2025-01-01", "2025-01-02"],
            "trade_type": ["buy", "sell"],
            "quantity": [100.0, 50.0],
            "price": [10.0, 12.0],
        })

        result = parser.parse(df)

        assert len(result) == 2
        assert result[0].transaction_type == "BUY"
        assert result[1].transaction_type == "SELL"

    def test_parse_date_validation(self, parser):
        """Test date parsing."""
        assert parser._parse_date("2025-01-15") == "2025-01-15"
        assert parser._parse_date("2024-12-31") == "2024-12-31"
        assert parser._parse_date("invalid") is None
        assert parser._parse_date("") is None
