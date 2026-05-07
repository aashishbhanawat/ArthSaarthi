# ruff: noqa: E501
from unittest.mock import MagicMock

import pytest

from app.services.import_parsers.hdfc_fd_parser import HdfcFdParser


@pytest.fixture
def parser():
    return HdfcFdParser()


def test_hdfc_fd_parser_valid_text(parser, monkeypatch):
    """Test parsing HDFC FD statement with valid text matching the format."""
    mock_pdfplumber = MagicMock()
    mock_open = MagicMock(return_value=mock_pdfplumber)
    mock_pdfplumber.__enter__.return_value = mock_pdfplumber

    mock_page = MagicMock()
    mock_page.extract_text.return_value = """
FD Details :- FOR CURRENT FINANCIAL YEAR
FD Number Open/Last Renew Date Maturity Date Rate of Interest Maturity Amount Available Withdrawable
12345678901234 01/01/2023 6.50 0.00 120000.00 YES
100000.00 01/01/2026 100000.00
98765432109876 15-06-2022 7.10 0.00 50000.00 YES
50000.00 15-06-2025 50000.00
"""
    mock_pdfplumber.pages = [mock_page]

    monkeypatch.setattr("pdfplumber.open", mock_open)

    fds = parser.parse("dummy.pdf", "password")

    assert len(fds) == 2

    # Check first FD (Cumulative)
    assert fds[0].bank == "HDFC"
    assert fds[0].account_number == "12345678901234"
    assert fds[0].start_date.strftime("%Y-%m-%d") == "2023-01-01"
    assert fds[0].maturity_date.strftime("%Y-%m-%d") == "2026-01-01"
    assert fds[0].principal_amount == 100000.0
    assert fds[0].maturity_amount == 120000.0
    assert fds[0].interest_rate == 6.50
    assert fds[0].interest_payout == "Cumulative"

    # Check 2nd FD (Payout)
    assert fds[1].account_number == "98765432109876"
    assert fds[1].start_date.strftime("%Y-%m-%d") == "2022-06-15"
    assert fds[1].principal_amount == 50000.0
    assert fds[1].maturity_amount == 50000.0
    assert fds[1].interest_rate == 7.10
    assert fds[1].interest_payout == "Payout"


def test_hdfc_fd_parser_password_required(parser, monkeypatch):
    """Test that ValueError("PASSWORD_REQUIRED") is raised if no password provided."""
    def mock_open(*args, **kwargs):
        raise ValueError("PASSWORD_REQUIRED")

    monkeypatch.setattr("pdfplumber.open", mock_open)

    with pytest.raises(ValueError) as excinfo:
        parser.parse("dummy.pdf")
    assert "PASSWORD_REQUIRED" in str(excinfo.value)
