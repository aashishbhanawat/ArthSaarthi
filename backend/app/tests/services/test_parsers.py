import pandas as pd

from app.schemas.import_session import ParsedTransaction
from app.services.import_parsers.zerodha_parser import ZerodhaParser


def test_zerodha_parser_success():
    # 1. Setup
    parser = ZerodhaParser()
    data = {
        "symbol": ["RELIANCE", "TCS"],
        "trade_date": ["2023-01-01", "2023-01-02"],
        "trade_type": ["buy", "sell"],
        "quantity": [10.0, 5.0],
        "price": [2500.0, 3300.0],
        "charges": [50.0, 25.0],
    }
    df = pd.DataFrame(data)

    # 2. Execute
    result = parser.parse(df)

    # 3. Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(tx, ParsedTransaction) for tx in result)

    # Check first transaction
    assert result[0].ticker_symbol == "RELIANCE"
    assert result[0].transaction_type == "BUY"
    assert result[0].quantity == 10.0
    assert result[0].price_per_unit == 2500.0
    assert result[0].fees == 50.0
    assert result[0].transaction_date == "2023-01-01"

    # Check second transaction
    assert result[1].ticker_symbol == "TCS"
    assert result[1].transaction_type == "SELL"


def test_zerodha_parser_ignores_other_types():
    # 1. Setup
    parser = ZerodhaParser()
    data = {
        "symbol": ["RELIANCE"],
        "trade_date": ["2023-01-01"],
        "trade_type": ["corporate action"],  # This should be ignored
        "quantity": [10.0],
        "price": [2500.0],
        "charges": [50.0],
    }
    df = pd.DataFrame(data)

    # 2. Execute
    result = parser.parse(df)

    # 3. Assert
    assert isinstance(result, list)
    assert len(result) == 0


def test_zerodha_parser_missing_columns():
    # 1. Setup
    parser = ZerodhaParser()
    data = {"symbol": ["RELIANCE"], "quantity": [10.0]}  # Missing columns
    df = pd.DataFrame(data)

    # 2. Execute
    result = parser.parse(df)

    # 3. Assert
    assert isinstance(result, list)
    assert len(result) == 0
