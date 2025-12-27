"""
Unit tests for KFintech PDF Parser.
"""
import pytest

from app.services.import_parsers.kfintech_parser import KFintechParser


@pytest.fixture
def parser():
    """Create a KFintechParser instance."""
    return KFintechParser()


class TestKFintechParser:
    """Test suite for KFintechParser."""

    def test_parse_date_format(self, parser):
        """Test date parsing."""
        assert parser._parse_date("29-Nov-2021") == "2021-11-29"
        assert parser._parse_date("01-Jan-2024") == "2024-01-01"
        assert parser._parse_date("15-Mar-2023") == "2023-03-15"
        assert parser._parse_date("invalid") is None

    def test_classify_transaction_buy(self, parser):
        """Test BUY transaction classification."""
        assert parser._classify_transaction("Purchase") == "BUY"
        assert parser._classify_transaction("SIP Purchase") == "BUY"
        assert parser._classify_transaction("Switch In") == "BUY"
        assert parser._classify_transaction("Systematic Investment") == "BUY"

    def test_classify_transaction_sell(self, parser):
        """Test SELL transaction classification."""
        assert parser._classify_transaction("Redemption") == "SELL"
        assert parser._classify_transaction("Switch Out") == "SELL"

    def test_classify_transaction_dividend(self, parser):
        """Test dividend transaction classification."""
        assert parser._classify_transaction(
            "IDCW Reinvestment"
        ) == "IDCW_REINVEST"
        assert parser._classify_transaction("IDCW Payout") == "DIVIDEND"
        assert parser._classify_transaction("Dividend Paid") == "DIVIDEND"

    def test_classify_transaction_unknown(self, parser):
        """Test unknown transaction returns None."""
        assert parser._classify_transaction("Unknown Type") is None
        assert parser._classify_transaction("Random Text") is None

    def test_should_skip_stamp_duty(self, parser):
        """Test stamp duty rows are skipped."""
        assert parser._should_skip("*** Stamp Duty ***")
        assert parser._should_skip("*** TDS Deducted ***")

    def test_should_skip_balance_rows(self, parser):
        """Test balance rows are skipped."""
        assert parser._should_skip("Opening Unit Balance 0.000")
        assert parser._should_skip("Closing Unit Balance: 1,234.56")

    def test_should_skip_header_rows(self, parser):
        """Test header rows are skipped."""
        assert parser._should_skip("Folio No : 123456")
        assert parser._should_skip("PAN: XXXXX0000X")
        assert parser._should_skip("KYC : OK")
        assert parser._should_skip("Nominee 1 : Test")

    def test_should_skip_merger(self, parser):
        """Test merger transactions are skipped."""
        assert parser._should_skip("Switch In - Merger")
        assert parser._should_skip("Switch Out - Merger")

    def test_should_not_skip_transaction(self, parser):
        """Test transaction lines are not skipped."""
        assert not parser._should_skip("29-Nov-2021 Purchase 50000")
        assert not parser._should_skip("15-Jan-2022 SIP Purchase 2000")

    def test_parse_number(self, parser):
        """Test number parsing with commas."""
        assert parser._parse_number("50,000.00") == 50000.00
        assert parser._parse_number("1,234.56") == 1234.56
        assert parser._parse_number("-100.50") == -100.50
        assert parser._parse_number("999") == 999.0

    def test_extract_scheme_name(self, parser):
        """Test scheme name extraction from header."""
        line = "ABC-Test Fund Direct Growth (Advisor:ARN-1234) - ISIN:INF123"
        assert "Test Fund Direct Growth" in parser._extract_scheme_name(line)
