# ruff: noqa: E501
from unittest.mock import MagicMock

import pytest

from app.services.import_parsers.icici_fd_parser import IciciFdParser


@pytest.fixture
def parser():
    return IciciFdParser()


def test_icici_fd_parser_valid_text(parser, monkeypatch):
    """Test parsing ICICI FD statement with valid text matching the format."""
    mock_pdfplumber = MagicMock()
    mock_open = MagicMock(return_value=mock_pdfplumber)
    mock_pdfplumber.__enter__.return_value = mock_pdfplumber

    # Note: ICICI typical line formatting from assumed fields
    mock_page = MagicMock()
    mock_page.extract_text.return_value = """
FIXED DEPOSITS - INR
ACCOUNT HOLDERS :
DEPOSIT NO. OPEN DATE PRINCIPAL ROI% MAT. AMOUNT MAT. DATE
000123456789 05-10-2021 500,000.00 5.25% 645000.00 05-10-2026 500,000.00 Registered
000987654321 12/12/2023 100,000.00 6.00 12/12/2025
"""
    mock_pdfplumber.pages = [mock_page]

    monkeypatch.setattr("pdfplumber.open", mock_open)

    fds = parser.parse("dummy.pdf", "password")

    assert len(fds) == 2

    # Check first FD (Cumulative)
    assert fds[0].bank == "ICICI"
    assert fds[0].account_number == "000123456789"
    assert fds[0].start_date == "2021-10-05"
    assert fds[0].maturity_date == "2026-10-05"
    assert fds[0].principal_amount == 500000.0
    assert fds[0].maturity_amount == 645000.0
    assert fds[0].interest_rate == 5.25
    assert fds[0].interest_payout == "Cumulative"

    # Check 2nd FD (missing mat amount defaults to principal = Payout)
    assert fds[1].account_number == "000987654321"
    assert fds[1].start_date == "2023-12-12"
    assert fds[1].maturity_date == "2025-12-12"
    assert fds[1].principal_amount == 100000.0
    assert fds[1].maturity_amount == 100000.0  # Defaulted
    assert fds[1].interest_rate == 6.0
    assert fds[1].interest_payout == "Payout"


def test_icici_fd_parser_password_required(parser, monkeypatch):
    """Test that ValueError("PASSWORD_REQUIRED") is raised if no password provided."""
    def mock_open(*args, **kwargs):
        raise ValueError("PASSWORD_REQUIRED")

    monkeypatch.setattr("pdfplumber.open", mock_open)

    with pytest.raises(ValueError) as excinfo:
        parser.parse("dummy.pdf")
    assert "PASSWORD_REQUIRED" in str(excinfo.value)
