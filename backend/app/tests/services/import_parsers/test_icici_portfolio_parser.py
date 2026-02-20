
import pandas as pd
import pytest

from app.services.import_parsers.icici_portfolio_parser import IciciPortfolioParser


@pytest.fixture
def parser():
    return IciciPortfolioParser()


def test_parse_valid_csv_data(parser):
    """Test parsing logic with valid data matching CSV format."""
    # Data from user sample
    data = {
        "Stock Symbol": ["ABAOFF", "GESHIP", "POWFIN"],
        "Company Name": ["ABAN OFFSHORE LTD", "GREAT EASTERN SHIPPING", "PFC"],
        "ISIN Code": ["INE421A01028", "INE017A01032", "INE134E01011"],
        "Action": ["Buy", "Buy", "Buy"],
        "Quantity": [30, 60, 75],
        "Transaction Price": [290.00, 883.50, 160.00],
        "Brokerage": [54.55, 75.36, 75.90],
        "Transaction Charges": [0.29, 1.68, 0.40],
        "StampDuty": [0.87, 8.00, 1.20],
        "Segment": ["Rolling", "TT", "Rolling"],
        "STT Paid/Not Paid": ["STT Paid", "STT Paid", "STT Paid"],
        "Remarks": ["icicidirect", "icicidirect", "icicidirect"],
        "Transaction Date": ["08-Jul-2015", "11-Feb-2025", "13-Jun-2016"],
        "Exchange": ["BSE", "NSE", "BSE"],
    }
    df = pd.DataFrame(data)

    transactions = parser.parse(df)

    assert len(transactions) == 3

    # Check 1st transaction
    t1 = transactions[0]
    assert t1.ticker_symbol == "ABAOFF"
    assert t1.isin == "INE421A01028"
    assert t1.transaction_date == "2015-07-08"
    assert t1.transaction_type == "BUY"
    assert t1.quantity == 30.0
    assert t1.price_per_unit == 290.0
    # Fees = 54.55 + 0.29 + 0.87 = 55.71
    assert abs(t1.fees - 55.71) < 0.01

    # Check 2nd transaction
    t2 = transactions[1]
    assert t2.ticker_symbol == "GESHIP"
    assert t2.isin == "INE017A01032"
    assert t2.transaction_date == "2025-02-11"

def test_parse_excludes_invalid_actions(parser):
    """Test ignoring actions other than Buy/Sell logic if applicable."""
    data = {
        "Stock Symbol": ["TEST"],
        "Action": ["Dividend"], # parser only filters for BUY/SELL
        "Quantity": [10],
        "Transaction Price": [100],
        "Transaction Date": ["01-Jan-2024"],
        "ISIN Code": ["INE123"],
        "Brokerage": [0],
        "Transaction Charges": [0],
        "StampDuty": [0]
    }
    df = pd.DataFrame(data)
    transactions = parser.parse(df)
    assert len(transactions) == 0

def test_parse_missing_fees_defaults_to_zero(parser):
    """Test logic handles missing logic columns gracefully."""
    data = {
        "Stock Symbol": ["TEST"],
        "Action": ["Buy"],
        "Quantity": [10],
        "Transaction Price": [100],
        "Transaction Date": ["01-Jan-2024"],
        "ISIN Code": ["INE123"],
        # No fee columns
    }
    df = pd.DataFrame(data)
    transactions = parser.parse(df)
    assert len(transactions) == 1
    assert transactions[0].fees == 0.0

def test_parse_handles_whitespace_in_headers(parser):
    """Test stripping logic for headers."""
    data = {
        " Stock Symbol ": ["TEST"],
        " Action": ["Buy"],
        "Quantity ": [10],
        " Transaction Price": [100],
        "Transaction Date": ["01-Jan-2024"],
        " ISIN Code ": ["INE123"],
        " Brokerage ": [10],
        "Transaction Charges": [0],
        "StampDuty": [0]
    }
    df = pd.DataFrame(data)
    transactions = parser.parse(df)
    assert len(transactions) == 1
    assert transactions[0].ticker_symbol == "TEST"
    assert transactions[0].fees == 10.0
