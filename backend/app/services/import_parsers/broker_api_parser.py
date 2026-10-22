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
    """Converts Zerodha Kite API holdings or trades JSON list into standard ArthSaarthi import transaction items.

    NOTE: Zerodha's /portfolio/holdings API returns a current-day snapshot.
    It does NOT provide the original buy/purchase date for holdings.
    The `authorised_date` field is the DDPI/TPIN authorization date (for
    demat selling permission), NOT the purchase date.
    For accurate buy dates, use the "Trade Book History" import mode instead.
    """
    parsed_items: List[Dict[str, Any]] = []

    if import_type == "holdings":
        # Log first raw item for diagnostics so we can inspect actual fields
        if raw_data:
            logger.debug(
                "Zerodha holdings raw sample (first item keys): %s",
                list(raw_data[0].keys()) if raw_data else "empty",
            )
            logger.debug("Zerodha holdings raw sample (first item): %s", raw_data[0])

        # Zerodha holdings API is a snapshot — buy dates are NOT available.
        # Use the user-provided as_of_date or fall back to today's date.
        snapshot_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
        if not as_of_date:
            logger.info(
                "Zerodha holdings snapshot: no as_of_date provided, using today's date (%s). "
                "Holdings API does not return original buy dates. "
                "For accurate transaction dates, use Trade Book History mode.",
                snapshot_date,
            )

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
                    "transaction_date": snapshot_date,
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


def _parse_icici_date_string(date_val: Any) -> Optional[str]:
    """Parses various date/time formats returned by ICICI Breeze API (e.g. '06-May-2024 13:42' or ISO)."""
    if not date_val:
        return None
    date_str = str(date_val).strip()
    for fmt in (
        "%d-%b-%Y %H:%M",
        "%d-%b-%Y %H:%M:%S",
        "%d-%b-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return None


def parse_icici_api_payload(
    raw_data: List[Dict[str, Any]],
    import_type: str = "holdings",
    default_portfolio_id: Optional[str] = None,
    as_of_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Converts ICICI Breeze API holdings or trades/orders JSON list into standard ArthSaarthi import transaction items.

    NOTE: ICICI Breeze's /portfolioholdings API returns a current-day snapshot.
    It does NOT provide the original buy/purchase date for holdings.
    For accurate buy dates, use the "Trade Book History" import mode instead.
    """
    parsed_items: List[Dict[str, Any]] = []

    if import_type == "holdings":
        # Log first raw item for diagnostics so we can inspect actual fields
        if raw_data:
            logger.debug(
                "ICICI holdings raw sample (first item keys): %s",
                list(raw_data[0].keys()) if raw_data else "empty",
            )
            logger.debug("ICICI holdings raw sample (first item): %s", raw_data[0])

        # ICICI holdings API is a snapshot — buy dates are NOT available.
        # Use the user-provided as_of_date or fall back to today's date.
        snapshot_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
        if not as_of_date:
            logger.info(
                "ICICI holdings snapshot: no as_of_date provided, using today's date (%s). "
                "Holdings API does not return original buy dates. "
                "For accurate transaction dates, use Trade Book History mode.",
                snapshot_date,
            )

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
                    "transaction_date": snapshot_date,
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
        if raw_data:
            logger.debug(
                "ICICI trades/orderlist raw sample (first item keys): %s",
                list(raw_data[0].keys()) if raw_data else "empty",
            )
            logger.debug("ICICI trades/orderlist raw sample (first item): %s", raw_data[0])

        for item in raw_data:
            stock_code = (item.get("stock_code") or item.get("stock_name") or "").upper()
            if not stock_code:
                continue

            exchange = (item.get("exchange_code") or "NSE").upper()

            # Status filter: for orderlist responses, filter for executed orders
            status_str = str(item.get("status") or item.get("order_status") or "").upper()
            if status_str and status_str not in (
                "EXECUTED",
                "PARTIALLY EXECUTED",
                "COMPLETE",
                "COMPLETED",
                "E",
                "P",
            ):
                continue

            action = (item.get("action") or item.get("order_flow") or item.get("transaction_type") or "BUY").upper()
            qty = Decimal(str(item.get("quantity") or item.get("executed_quantity") or 0))
            if qty <= 0:
                continue

            # In Breeze orderlist, executed orders have average_price; fall back to price
            avg_price_val = item.get("average_price")
            price_val = item.get("price")
            price = Decimal(str(avg_price_val if avg_price_val and str(avg_price_val) != "0" else price_val or 0))
            if price <= 0:
                continue

            trade_date_raw = (
                item.get("order_datetime")
                or item.get("trade_date")
                or item.get("execution_time")
                or item.get("date")
                or item.get("exchange_acknowledgement_date")
                or ""
            )

            tx_date = _parse_icici_date_string(trade_date_raw) or as_of_date or datetime.now().strftime("%Y-%m-%d")

            ticker_symbol = f"{stock_code}.BO" if exchange == "BSE" else f"{stock_code}.NS"
            amount = qty * price
            tx_type = "SELL" if "SELL" in action or action == "S" else "BUY"

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
