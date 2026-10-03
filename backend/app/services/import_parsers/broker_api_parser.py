import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_zerodha_api_payload(
    raw_data: List[Dict[str, Any]],
    import_type: str = "holdings",
    default_portfolio_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Converts Zerodha Kite API holdings or trades JSON list into standard ArthSaarthi import transaction items."""
    parsed_items: List[Dict[str, Any]] = []

    if import_type == "holdings":
        for item in raw_data:
            symbol = item.get("tradingsymbol", "").upper()
            exchange = item.get("exchange", "NSE").upper()
            qty = Decimal(str(item.get("quantity") or 0))
            avg_price = Decimal(str(item.get("average_price") or 0))
            isin = item.get("isin", "")

            if qty <= 0:
                continue

            ticker_symbol = f"{symbol}.BO" if exchange == "BSE" else f"{symbol}.NS"
            amount = qty * avg_price

            parsed_items.append(
                {
                    "transaction_date": datetime.now().strftime("%Y-%m-%d"),
                    "symbol": ticker_symbol,
                    "name": symbol,
                    "transaction_type": "BUY",
                    "quantity": float(qty),
                    "price": float(avg_price),
                    "amount": float(amount),
                    "fees": 0.0,
                    "asset_type": "STOCK",
                    "exchange": exchange,
                    "isin": isin,
                    "portfolio_id": default_portfolio_id,
                    "source": "zerodha_api",
                }
            )

    elif import_type == "trades":
        for item in raw_data:
            symbol = item.get("tradingsymbol", "").upper()
            exchange = item.get("exchange", "NSE").upper()
            tx_type = item.get("transaction_type", "BUY").upper()
            qty = Decimal(str(item.get("quantity") or 0))
            price = Decimal(str(item.get("average_price") or item.get("price") or 0))
            fill_ts = item.get("fill_timestamp") or item.get("trade_date") or ""

            if fill_ts:
                try:
                    tx_date = datetime.fromisoformat(str(fill_ts).replace("Z", "+00:00")).strftime("%Y-%m-%d")
                except Exception:
                    tx_date = datetime.now().strftime("%Y-%m-%d")
            else:
                tx_date = datetime.now().strftime("%Y-%m-%d")

            ticker_symbol = f"{symbol}.BO" if exchange == "BSE" else f"{symbol}.NS"
            amount = qty * price

            parsed_items.append(
                {
                    "transaction_date": tx_date,
                    "symbol": ticker_symbol,
                    "name": symbol,
                    "transaction_type": tx_type if tx_type in ("BUY", "SELL") else "BUY",
                    "quantity": float(qty),
                    "price": float(price),
                    "amount": float(amount),
                    "fees": 0.0,
                    "asset_type": "STOCK",
                    "exchange": exchange,
                    "isin": "",
                    "portfolio_id": default_portfolio_id,
                    "source": "zerodha_api",
                }
            )

    return parsed_items


def parse_icici_api_payload(
    raw_data: List[Dict[str, Any]],
    import_type: str = "holdings",
    default_portfolio_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Converts ICICI Breeze API holdings or trades JSON list into standard ArthSaarthi import transaction items."""
    parsed_items: List[Dict[str, Any]] = []

    if import_type == "holdings":
        for item in raw_data:
            stock_code = (item.get("stock_code") or item.get("stock_name") or "").upper()
            exchange = (item.get("exchange_code") or "NSE").upper()
            qty = Decimal(str(item.get("quantity") or 0))
            avg_price = Decimal(str(item.get("average_price") or item.get("average_cost") or 0))

            if qty <= 0:
                continue

            ticker_symbol = f"{stock_code}.BO" if exchange == "BSE" else f"{stock_code}.NS"
            amount = qty * avg_price

            parsed_items.append(
                {
                    "transaction_date": datetime.now().strftime("%Y-%m-%d"),
                    "symbol": ticker_symbol,
                    "name": stock_code,
                    "transaction_type": "BUY",
                    "quantity": float(qty),
                    "price": float(avg_price),
                    "amount": float(amount),
                    "fees": 0.0,
                    "asset_type": "STOCK",
                    "exchange": exchange,
                    "isin": "",
                    "portfolio_id": default_portfolio_id,
                    "source": "icici_breeze_api",
                }
            )

    elif import_type == "trades":
        for item in raw_data:
            stock_code = (item.get("stock_code") or "").upper()
            exchange = (item.get("exchange_code") or "NSE").upper()
            action = (item.get("action") or item.get("transaction_type") or "BUY").upper()
            qty = Decimal(str(item.get("quantity") or 0))
            price = Decimal(str(item.get("price") or item.get("average_price") or 0))
            trade_date_raw = item.get("trade_date") or item.get("execution_time") or ""

            if trade_date_raw:
                try:
                    tx_date = datetime.fromisoformat(str(trade_date_raw).replace("Z", "+00:00")).strftime("%Y-%m-%d")
                except Exception:
                    tx_date = datetime.now().strftime("%Y-%m-%d")
            else:
                tx_date = datetime.now().strftime("%Y-%m-%d")

            ticker_symbol = f"{stock_code}.BO" if exchange == "BSE" else f"{stock_code}.NS"
            amount = qty * price
            tx_type = "SELL" if "SELL" in action or "S" == action else "BUY"

            parsed_items.append(
                {
                    "transaction_date": tx_date,
                    "symbol": ticker_symbol,
                    "name": stock_code,
                    "transaction_type": tx_type,
                    "quantity": float(qty),
                    "price": float(price),
                    "amount": float(amount),
                    "fees": 0.0,
                    "asset_type": "STOCK",
                    "exchange": exchange,
                    "isin": "",
                    "portfolio_id": default_portfolio_id,
                    "source": "icici_breeze_api",
                }
            )

    return parsed_items
