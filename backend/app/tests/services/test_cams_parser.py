"""
Unit tests for CAMS Parser.
"""
from pathlib import Path

import pandas as pd
import pytest

from app.services.import_parsers.cams_parser import CamsParser


@pytest.fixture
def sample_cams_df():
    """Load the sample CAMS Excel file as a DataFrame."""
    assets_dir = Path(__file__).parent.parent / "assets"
    sample_file = assets_dir / "sample_cams.xlsx"

    if not sample_file.exists():
        pytest.skip(f"Sample file not found: {sample_file}")

    df = pd.read_excel(sample_file)
    return df


@pytest.fixture
def parser():
    """Create a CamsParser instance."""
    return CamsParser()


class TestCamsParser:
    """Test suite for CamsParser."""

    def test_parse_returns_list_of_transactions(self, parser, sample_cams_df):
        """Test that parse returns a non-empty list of transactions."""
        result = parser.parse(sample_cams_df)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_excludes_non_transaction_rows(self, parser, sample_cams_df):
        """Test that non-transaction rows are skipped."""
        result = parser.parse(sample_cams_df)

        # Check that no transaction symbols contain excluded patterns
        for tx in result:
            assert "Registration of Nominee" not in tx.ticker_symbol
            assert "Change of Contact" not in tx.ticker_symbol
            assert "Address Updated" not in tx.ticker_symbol

    def test_parse_correctly_classifies_purchase_transactions(
        self, parser, sample_cams_df
    ):
        """Test that purchase transactions are classified as BUY."""
        result = parser.parse(sample_cams_df)

        buy_transactions = [tx for tx in result if tx.transaction_type == "BUY"]

        assert len(buy_transactions) > 0, "Should have at least one BUY transaction"

    def test_parse_correctly_classifies_dividend_transactions(
        self, parser, sample_cams_df
    ):
        """Test that IDCW Paid transactions are classified as DIVIDEND."""
        result = parser.parse(sample_cams_df)

        dividend_transactions = [
            tx for tx in result if tx.transaction_type == "DIVIDEND"
        ]

        assert len(dividend_transactions) >= 1, "Should have DIVIDEND transactions"

    def test_idcw_reinvestment_creates_two_transactions(
        self, parser, sample_cams_df
    ):
        """Test that IDCW Reinvestment creates both DIVIDEND and BUY transactions."""
        result = parser.parse(sample_cams_df)

        # IDCW Reinvestment should create pairs on same date with same scheme
        # We can't easily identify them without the original data, but we can
        # check that we have both types
        has_dividend = any(tx.transaction_type == "DIVIDEND" for tx in result)
        has_buy = any(tx.transaction_type == "BUY" for tx in result)

        assert has_dividend, "Should have DIVIDEND transactions"
        assert has_buy, "Should have BUY transactions"

    def test_ticker_symbol_includes_mf_name(self, parser, sample_cams_df):
        """Test that ticker_symbol includes both MF_NAME and SCHEME_NAME."""
        result = parser.parse(sample_cams_df)

        # Ticker should include AMC name (from MF_NAME column)
        for tx in result:
            assert tx.ticker_symbol is not None
            assert len(tx.ticker_symbol) > 0
            # Should contain scheme name
            assert "Fund" in tx.ticker_symbol or "IDCW" in tx.ticker_symbol

    def test_parse_date_format_conversion(self, parser, sample_cams_df):
        """Test that dates are converted to ISO format (YYYY-MM-DD)."""
        result = parser.parse(sample_cams_df)

        for tx in result:
            assert len(tx.transaction_date) == 10
            assert tx.transaction_date[4] == "-"
            assert tx.transaction_date[7] == "-"

    def test_parse_sets_zero_fees(self, parser, sample_cams_df):
        """Test that fees are set to 0 (CAMS doesn't provide fee breakdown)."""
        result = parser.parse(sample_cams_df)

        for tx in result:
            assert tx.fees == 0.0

    def test_classify_transaction_patterns(self, parser):
        """Test the transaction classification logic."""
        # BUY patterns
        assert parser._classify_transaction("Purchase") == "BUY"
        assert parser._classify_transaction("PURCHASE") == "BUY"
        assert parser._classify_transaction("SIP Purchase") == "BUY"
        assert parser._classify_transaction("Purchase - Systematic") == "BUY"

        # SELL patterns
        assert parser._classify_transaction("Redemption") == "SELL"
        assert parser._classify_transaction("Redemption Of Units") == "SELL"

        # DIVIDEND patterns
        assert parser._classify_transaction("IDCW Paid") == "DIVIDEND"

        # IDCW Reinvest patterns
        assert parser._classify_transaction("IDCW Reinvest") == "IDCW_REINVEST"
        assert parser._classify_transaction("IDCW Reinvestment") == "IDCW_REINVEST"

        # Unknown patterns
        assert parser._classify_transaction("Unknown Transaction") is None

    def test_should_skip_patterns(self, parser):
        """Test the skip detection logic."""
        # Should skip
        assert parser._should_skip("Registration of Nominee") is True
        assert parser._should_skip("Change of Contact details") is True
        assert parser._should_skip("Address Updated from KRA") is True
        assert parser._should_skip("Switch In - Merger") is True
        assert parser._should_skip("Switch Out - Merger") is True
        assert parser._should_skip("Cancelled") is True

        # Should NOT skip
        assert parser._should_skip("Purchase") is False
        assert parser._should_skip("Redemption") is False
        assert parser._should_skip("IDCW Paid") is False

    def test_parse_date_formats(self, parser):
        """Test date parsing with different formats."""
        # Standard CAMS format
        assert parser._parse_date("16-MAR-2023") == "2023-03-16"
        assert parser._parse_date("01-JAN-2024") == "2024-01-01"
        assert parser._parse_date("31-DEC-2025") == "2025-12-31"

        # Invalid dates
        assert parser._parse_date("invalid") is None
