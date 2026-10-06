from decimal import Decimal
from app.services.import_parsers.broker_api_parser import (
    parse_zerodha_api_payload,
    parse_icici_api_payload,
)


def test_parse_zerodha_api_holdings():
    mock_raw = [
        {
            "tradingsymbol": "INFY",
            "exchange": "NSE",
            "quantity": 10,
            "average_price": 1450.50,
            "isin": "INE009A01021",
        },
        {
            "tradingsymbol": "TCS",
            "exchange": "BSE",
            "quantity": 5,
            "average_price": 3500.00,
            "isin": "INE467B01029",
        },
    ]

    res = parse_zerodha_api_payload(mock_raw, import_type="holdings")
    assert len(res) == 2
    assert res[0]["ticker_symbol"] == "INFY.NS"
    assert res[0]["symbol"] == "INFY.NS"
    assert res[0]["quantity"] == 10.0
    assert res[0]["price_per_unit"] == 1450.50
    assert res[0]["price"] == 1450.50
    assert res[0]["source"] == "zerodha_api"
    assert res[1]["ticker_symbol"] == "TCS.BO"
    assert res[1]["symbol"] == "TCS.BO"


def test_parse_zerodha_api_trades():
    mock_raw = [
        {
            "tradingsymbol": "RELIANCE",
            "exchange": "NSE",
            "transaction_type": "BUY",
            "quantity": 20,
            "average_price": 2400.00,
            "fill_timestamp": "2026-03-15T10:30:00Z",
        }
    ]

    res = parse_zerodha_api_payload(mock_raw, import_type="trades")
    assert len(res) == 1
    assert res[0]["ticker_symbol"] == "RELIANCE.NS"
    assert res[0]["symbol"] == "RELIANCE.NS"
    assert res[0]["transaction_type"] == "BUY"
    assert res[0]["quantity"] == 20.0
    assert res[0]["price_per_unit"] == 2400.00
    assert res[0]["transaction_date"] == "2026-03-15"


def test_parse_icici_api_holdings():
    mock_raw = [
        {
            "stock_code": "INFTEC",
            "exchange_code": "NSE",
            "quantity": 15,
            "average_price": 1500.00,
        }
    ]

    res = parse_icici_api_payload(mock_raw, import_type="holdings")
    assert len(res) == 1
    assert res[0]["ticker_symbol"] == "INFTEC.NS"
    assert res[0]["symbol"] == "INFTEC.NS"
    assert res[0]["quantity"] == 15.0
    assert res[0]["price_per_unit"] == 1500.00
    assert res[0]["source"] == "icici_breeze_api"


def test_parse_icici_api_trades():
    mock_raw = [
        {
            "stock_code": "TATMOT",
            "exchange_code": "NSE",
            "action": "SELL",
            "quantity": 50,
            "price": 650.00,
            "trade_date": "2026-04-10T14:15:00Z",
        }
    ]

    res = parse_icici_api_payload(mock_raw, import_type="trades")
    assert len(res) == 1
    assert res[0]["ticker_symbol"] == "TATMOT.NS"
    assert res[0]["symbol"] == "TATMOT.NS"
    assert res[0]["transaction_type"] == "SELL"
    assert res[0]["quantity"] == 50.0
    assert res[0]["price_per_unit"] == 650.00
    assert res[0]["transaction_date"] == "2026-04-10"
