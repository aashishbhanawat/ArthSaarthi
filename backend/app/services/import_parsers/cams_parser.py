"""
CAMS Excel Parser.

Parses Mutual Fund transaction Excel files exported from CAMSOnline.
Handles transactions including purchases, redemptions, SIPs, and dividends.
"""
import logging
import re
from datetime import datetime
from typing import List

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class CamsParser(BaseParser):
    """
    Parser for CAMS (Computer Age Management Services) Excel files.

    CAMS serves ~65% of Indian AMCs including HDFC, ICICI Prudential,
    DSP, Franklin Templeton, TATA, Kotak, and others.
    """

    # Transaction patterns for type classification
    TRANSACTION_PATTERNS = {
        "BUY": [
            r"^Purchase",
            r"^PURCHASE",
            r"^SIP Purchase",
            r"^Purchase - Systematic",
            r"^Systematic Investment Purchase",
        ],
        "SELL": [
            r"^Redemption",
        ],
        "DIVIDEND": [
            r"^IDCW Paid",
        ],
        # IDCW Reinvest handled specially - creates 2 transactions
        "IDCW_REINVEST": [
            r"^IDCW Reinvest",
            r"^IDCW Reinvestment",
        ],
    }

    # Patterns to skip (non-transaction rows)
    SKIP_PATTERNS = [
        r"^Registration of Nominee",
        r"^Change of Contact",
        r"^Change of Contacts",
        r"^Change / Regn of Nominee",
        r"^Address Updated",
        r"^Cancelled",
        r"^Upload Benposs",
        r"^Switch In - Merger",
        r"^Switch Out - Merger",
    ]

    # Expected columns in CAMS Excel
    EXPECTED_COLUMNS = [
        "MF_NAME",
        "SCHEME_NAME",
        "TRADE_DATE",
        "TRANSACTION_TYPE",
        "AMOUNT",
        "UNITS",
        "PRICE",
    ]

    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parse CAMS DataFrame into ParsedTransaction objects.
        """
        transactions = []

        # Check if columns exist (CAMS has headers in row 0)
        if not all(col in df.columns for col in self.EXPECTED_COLUMNS):
            logger.error(
                "CAMS parser: Missing required columns. Expected: %s, Found: %s",
                self.EXPECTED_COLUMNS,
                df.columns.tolist(),
            )
            return []

        for _, row in df.iterrows():
            try:
                mf_name = str(row.get("MF_NAME", "")).strip()
                scheme_name = str(row.get("SCHEME_NAME", "")).strip()
                tx_desc = str(row.get("TRANSACTION_TYPE", "")).strip()
                date_str = str(row.get("TRADE_DATE", "")).strip()
                amount = row.get("AMOUNT")
                units = row.get("UNITS")
                price = row.get("PRICE")

                # Skip empty rows
                if not scheme_name or scheme_name == "nan":
                    continue

                # Skip non-transaction rows
                if self._should_skip(tx_desc):
                    logger.debug("CAMS parser: Skipping row: %s", tx_desc)
                    continue

                # Classify transaction type
                tx_type = self._classify_transaction(tx_desc)
                if tx_type is None:
                    logger.debug(
                        "CAMS parser: Unknown transaction type: %s", tx_desc
                    )
                    continue

                # Parse numeric values
                try:
                    units_float = float(units) if units and str(units) != "nan" else 0.0
                    price_float = float(price) if price and str(price) != "nan" else 0.0
                    is_valid = amount and str(amount) != "nan"
                    amount_float = float(amount) if is_valid else 0.0
                except (ValueError, TypeError):
                    units_float = 0.0
                    price_float = 0.0
                    amount_float = 0.0

                # Skip rows with zero units and zero amount (admin updates)
                if units_float == 0 and amount_float == 0:
                    logger.debug("CAMS parser: Skipping zero row: %s", tx_desc)
                    continue

                # Parse date (format: DD-MMM-YYYY, e.g., "16-MAR-2023")
                transaction_date = self._parse_date(date_str)
                if transaction_date is None:
                    logger.warning(
                        "CAMS parser: Could not parse date: %s", date_str
                    )
                    continue

                # Merge MF_NAME and SCHEME_NAME for full fund name
                ticker_symbol = f"{mf_name} {scheme_name}".strip()

                # Handle IDCW Reinvestment - creates 2 transactions
                if tx_type == "IDCW_REINVEST":
                    # 1. DIVIDEND transaction (amount received)
                    if amount_float > 0:
                        transactions.append(ParsedTransaction(
                            ticker_symbol=ticker_symbol,
                            transaction_date=transaction_date,
                            transaction_type="DIVIDEND",
                            quantity=abs(amount_float),
                            price_per_unit=1.0,
                            fees=0.0,
                        ))
                    # 2. BUY transaction (units purchased)
                    if units_float > 0 and price_float > 0:
                        transactions.append(ParsedTransaction(
                            ticker_symbol=ticker_symbol,
                            transaction_date=transaction_date,
                            transaction_type="BUY",
                            quantity=abs(units_float),
                            price_per_unit=price_float,
                            fees=0.0,
                        ))
                elif tx_type == "DIVIDEND":
                    # IDCW Paid - only dividend, no units
                    transactions.append(ParsedTransaction(
                        ticker_symbol=ticker_symbol,
                        transaction_date=transaction_date,
                        transaction_type="DIVIDEND",
                        quantity=abs(amount_float),
                        price_per_unit=1.0,
                        fees=0.0,
                    ))
                else:
                    # Regular BUY/SELL transaction
                    transactions.append(ParsedTransaction(
                        ticker_symbol=ticker_symbol,
                        transaction_date=transaction_date,
                        transaction_type=tx_type,
                        quantity=abs(units_float),
                        price_per_unit=price_float,
                        fees=0.0,
                    ))

            except Exception as e:
                logger.error(
                    "CAMS parser: Error parsing row: %s. Error: %s",
                    row.to_dict() if hasattr(row, "to_dict") else str(row),
                    e,
                )

        logger.info("CAMS parser: Parsed %d transactions", len(transactions))
        return transactions

    def _classify_transaction(self, tx_desc: str) -> str | None:
        """Classify transaction into BUY, SELL, DIVIDEND, or IDCW_REINVEST."""
        for tx_type, patterns in self.TRANSACTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, tx_desc, re.IGNORECASE):
                    return tx_type
        return None

    def _should_skip(self, tx_desc: str) -> bool:
        """Check if this transaction description should be skipped."""
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, tx_desc, re.IGNORECASE):
                return True
        return False

    def _parse_date(self, date_str: str) -> str | None:
        """
        Parse date from CAMS format (DD-MMM-YYYY) to ISO format (YYYY-MM-DD).
        """
        if not date_str or date_str == "nan":
            return None

        try:
            # CAMS uses DD-MMM-YYYY format (e.g., "16-MAR-2023")
            parsed = datetime.strptime(date_str, "%d-%b-%Y")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass

        # Try alternative formats
        for fmt in ["%d-%B-%Y", "%Y-%m-%d", "%d/%m/%Y"]:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None
