import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_zerodha_api_payload(
    raw_data: List[Dict[str, Any]],
    import_type: str = "holdings",
    default_portfolio_id: Optional[str] = None,
    as_of_date: Optional[str] = None,
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

            item_date = (
                item.get("authorised_date")
                or item.get("created_date")
                or item.get("buy_date")
                or item.get("date")
                or item.get("order_timestamp")
            )
            if item_date:
                try:
                    tx_date = datetime.fromisoformat(str(item_date).replace("Z", "+00:00")).strftime("%Y-%m-%d")
                except Exception:
                    tx_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
            elif as_of_date:
                tx_date = as_of_date
            else:
                tx_date = datetime.now().strftime("%Y-%m-%d")

            parsed_items.append(
                {
                    "transaction_date": tx_date,
                    "ticker_symbol": ticker_symbol,
                    "symbol": ticker_symbol,
                    "name": symbol,
                    "transaction_type": "BUY",
                    "quantity": float(qty),
                    "price_per_unit": float(avg_price),
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
            fill_ts = item.get("fill_timestamp") or item.get("trade_date") or item.get("order_timestamp") or ""

            if fill_ts:
                try:
                    tx_date = datetime.fromisoformat(str(fill_ts).replace("Z", "+00:00")).strftime("%Y-%m-%d")
                except Exception:
                    tx_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
            elif as_of_date:
                tx_date = as_of_date
            else:
                tx_date = datetime.now().strftime("%Y-%m-%d")

            ticker_symbol = f"{symbol}.BO" if exchange == "BSE" else f"{symbol}.NS"
            amount = qty * price

            parsed_items.append(
                {
                    "transaction_date": tx_date,
                    "ticker_symbol": ticker_symbol,
                    "symbol": ticker_symbol,
                    "name": symbol,
                    "transaction_type": tx_type if tx_type in ("BUY", "SELL") else "BUY",
                    "quantity": float(qty),
                    "price_per_unit": float(price),
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
    as_of_date: Optional[str] = None,
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

            item_date = (
                item.get("trade_date")
                or item.get("order_date")
                or item.get("date")
                or item.get("execution_time")
            )
            if item_date:
                try:
                    tx_date = datetime.fromisoformat(str(item_date).replace("Z", "+00:00")).strftime("%Y-%m-%d")
                except Exception:
                    tx_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
            elif as_of_date:
                tx_date = as_of_date
            else:
                tx_date = datetime.now().strftime("%Y-%m-%d")

            parsed_items.append(
                {
                    "transaction_date": tx_date,
                    "ticker_symbol": ticker_symbol,
                    "symbol": ticker_symbol,
                    "name": stock_code,
                    "transaction_type": "BUY",
                    "quantity": float(qty),
                    "price_per_unit": float(avg_price),
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
                    tx_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
            elif as_of_date:
                tx_date = as_of_date
            else:
                tx_date = datetime.now().strftime("%Y-%m-%d")

            ticker_symbol = f"{stock_code}.BO" if exchange == "BSE" else f"{stock_code}.NS"
            amount = qty * price
            tx_type = "SELL" if "SELL" in action or "S" == action else "BUY"

            parsed_items.append(
                {
                    "transaction_date": tx_date,
                    "ticker_symbol": ticker_symbol,
                    "symbol": ticker_symbol,
                    "name": stock_code,
                    "transaction_type": tx_type,
                    "quantity": float(qty),
                    "price_per_unit": float(price),
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
