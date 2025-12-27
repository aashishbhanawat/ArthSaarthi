"""
Zerodha Coin MF Parser.

Parses Mutual Fund tradebook exports from Zerodha Coin (coin.zerodha.com).
Handles both CSV and Excel formats.
"""
import logging
from typing import List

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class ZerodhaCoinParser(BaseParser):
    """
    Parser for Zerodha Coin MF tradebook files.

    Zerodha Coin is a direct MF platform for purchasing mutual funds.
    Exports contain buy/sell transactions with scheme name, quantity, and NAV.
    """

    # Expected columns in Zerodha Coin export
    EXPECTED_COLUMNS = [
        "symbol",
        "trade_date",
        "trade_type",
        "quantity",
        "price",
    ]

    # Optional columns
    OPTIONAL_COLUMNS = ["isin"]

    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parse Zerodha Coin DataFrame into ParsedTransaction objects.
        """
        transactions = []

        # Check if required columns exist
        missing_cols = [
            col for col in self.EXPECTED_COLUMNS if col not in df.columns
        ]
        if missing_cols:
            logger.error(
                "Zerodha Coin parser: Missing columns: %s. Found: %s",
                missing_cols,
                df.columns.tolist(),
            )
            return []

        # Check if isin column exists for better matching
        has_isin = "isin" in df.columns
        if has_isin:
            logger.info("Zerodha Coin: ISIN column found, using for asset matching")

        for _, row in df.iterrows():
            try:
                symbol = str(row.get("symbol", "")).strip()
                isin = str(row.get("isin", "")).strip() if has_isin else ""
                trade_date = str(row.get("trade_date", "")).strip()
                trade_type = str(row.get("trade_type", "")).strip().lower()
                quantity = row.get("quantity")
                price = row.get("price")

                # Skip empty rows
                if not symbol or symbol == "nan":
                    continue

                # Classify transaction
                if trade_type == "buy":
                    tx_type = "BUY"
                elif trade_type == "sell":
                    tx_type = "SELL"
                else:
                    logger.debug(
                        "Zerodha Coin parser: Unknown trade_type: %s",
                        trade_type,
                    )
                    continue

                # Parse numeric values
                try:
                    qty = float(quantity) if quantity else 0.0
                    ppu = float(price) if price else 0.0
                except (ValueError, TypeError):
                    qty = 0.0
                    ppu = 0.0

                # Skip zero quantity rows
                if qty == 0:
                    continue

                # Date is already in YYYY-MM-DD format
                transaction_date = self._parse_date(trade_date)
                if transaction_date is None:
                    logger.warning(
                        "Zerodha Coin parser: Invalid date: %s", trade_date
                    )
                    continue

                # Use ISIN for ticker if available (enables auto-matching)
                if isin and len(isin) == 12 and isin.startswith("INF"):
                    ticker = f"ISIN:{isin}"
                else:
                    ticker = symbol

                transactions.append(ParsedTransaction(
                    ticker_symbol=ticker,
                    transaction_date=transaction_date,
                    transaction_type=tx_type,
                    quantity=abs(qty),
                    price_per_unit=ppu,
                    fees=0.0,
                ))

            except Exception as e:
                logger.error(
                    "Zerodha Coin parser: Error parsing row: %s. Error: %s",
                    row.to_dict() if hasattr(row, "to_dict") else str(row),
                    e,
                )

        logger.info(
            "Zerodha Coin parser: Parsed %d transactions", len(transactions)
        )
        return transactions

    def _parse_date(self, date_str: str) -> str | None:
        """
        Parse date - Zerodha uses YYYY-MM-DD format.
        """
        if not date_str or date_str == "nan":
            return None

        # Already in correct format, just validate
        parts = date_str.split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            return date_str

        return None
