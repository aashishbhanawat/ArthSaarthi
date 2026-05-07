# ruff: noqa: E501
from unittest.mock import MagicMock

import pytest

from app.services.import_parsers.sbi_fd_parser import SbiFdParser


@pytest.fixture
def parser():
    return SbiFdParser()


def test_sbi_fd_parser_valid_text(parser, monkeypatch):
    """Test parsing SBI FD statement with valid text matching the format."""
    mock_pdfplumber = MagicMock()
    mock_open = MagicMock(return_value=mock_pdfplumber)
    mock_pdfplumber.__enter__.return_value = mock_pdfplumber

    mock_page = MagicMock()
    mock_page.extract_text.return_value = """
FIXED DEPOSITS
TDR AND STDR ACCOUNTS CURRENCY: INR
Account Account Number Principal Holding ROI Lien/Hold Maturity Amount Maturity Date
Account Type Open Date Amount Status (%)** Amount Date*
TERM DEPOSIT XXXXXXX3276 07-12-15 26613.36 P 6.25 0.00 258.74 28316.00 07-12-26 Yes
TERM DEPOSIT XXXXXXX9904 09-05-16 54854.00 P 6.70 0.00 2720.24 58623.00 09-05-26 Yes
TERM DEPOSIT 12345678901 01-01-20 10000.00 P 7.00 0.00 0.00 10000.00 01-01-25 No
OTHER INVESTMENTS
"""
    mock_pdfplumber.pages = [mock_page]

    monkeypatch.setattr("pdfplumber.open", mock_open)

    fds = parser.parse("dummy.pdf", "password")

    assert len(fds) == 3

    # Check first FD (Cumulative)
    assert fds[0].bank == "SBI"
    assert fds[0].account_number == "XXXXXXX3276"
    assert fds[0].start_date == "2015-12-07"
    assert fds[0].maturity_date == "2026-12-07"
    assert fds[0].principal_amount == 26613.36
    assert fds[0].maturity_amount == 28316.00
    assert fds[0].interest_rate == 6.25
    assert fds[0].interest_payout == "Cumulative"
    assert fds[0].compounding_frequency == "Quarterly"

    # Check 3rd FD (Payout)
    assert fds[2].account_number == "12345678901"
    assert fds[2].principal_amount == 10000.0
    assert fds[2].maturity_amount == 10000.0
    assert fds[2].interest_payout == "Payout"


def test_sbi_fd_parser_password_required(parser, monkeypatch):
    """Test that ValueError("PASSWORD_REQUIRED") is raised if no password provided."""
    def mock_open(*args, **kwargs):
        raise ValueError("PASSWORD_REQUIRED")

    monkeypatch.setattr("pdfplumber.open", mock_open)

    with pytest.raises(ValueError) as excinfo:
        parser.parse("dummy.pdf")
    assert "PASSWORD_REQUIRED" in str(excinfo.value)
