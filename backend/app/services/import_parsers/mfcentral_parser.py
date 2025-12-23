"""
MFCentral CAS Excel Parser.

Parses Consolidated Account Statement (CAS) Excel files exported from MFCentral.
Handles Mutual Fund transactions including purchases, redemptions, SIPs, and dividends.
"""
import logging
import re
from typing import List

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class MfCentralParser(BaseParser):
    """
    Parser for MFCentral CAS (Consolidated Account Statement) Excel files.

    MFCentral provides MF transaction data from both CAMS and KFintech RTAs,
    covering transactions from January 2022 onwards.
    """

    # Transaction patterns for type classification
    TRANSACTION_PATTERNS = {
        "BUY": [
            r"^Purchase",
            r"^IDCW Reinvestment",
            r"^Switch In(?! - Merger)",  # Switch In but NOT Merger
        ],
        "SELL": [
            r"^Redemption",
            r"^Switch Out(?! - Merger)",  # Switch Out but NOT Merger
        ],
        "DIVIDEND": [
            r"^IDCW Paid",
        ],
    }

    # Patterns to skip (non-transaction rows)
    SKIP_PATTERNS = [
        r"^Registration of Nominee",
        r"^Change of Contact",
        r"^Address Updated",
        r"^Change / Regn of Nominee",
        r"^Switch In - Merger",  # Fund merger - skip for now
        r"^Switch Out - Merger",  # Fund merger - skip for now
    ]

    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parse MFCentral CAS DataFrame into ParsedTransaction objects.

        Note: Input DataFrame should have header=None as the CAS file
        has metadata rows before the actual headers.
        """
        transactions = []

        # Find the header row (contains "Scheme Name")
        header_row_idx = None
        for idx, row in df.iterrows():
            if "Scheme Name" in row.values:
                header_row_idx = idx
                break

        if header_row_idx is None:
            logger.error(
                "MFCentral parser: Could not find header row with 'Scheme Name'"
            )
            return []

        # Set headers from the found row
        df.columns = df.iloc[header_row_idx].values
        df = df.iloc[header_row_idx + 1:].reset_index(drop=True)

        # Track expected columns
        expected_columns = [
            "Scheme Name",
            "Transaction Description",
            "Date",
            "NAV",
            "Units",
            "Amount",
        ]

        # Check if columns exist
        if not all(col in df.columns for col in expected_columns):
            logger.error(
                "MFCentral parser: Missing required columns. Expected: %s, Found: %s",
                expected_columns,
                df.columns.tolist(),
            )
            return []

        for _, row in df.iterrows():
            try:
                scheme_name = str(row["Scheme Name"]).strip()
                tx_desc = str(row["Transaction Description"]).strip()
                date_str = str(row["Date"]).strip()
                nav = row["NAV"]
                units = row["Units"]
                amount = row["Amount"]

                # Skip rows with empty scheme name or transaction description
                if not scheme_name or scheme_name == "nan":
                    continue
                if not tx_desc or tx_desc == "nan":
                    continue

                # Skip non-transaction rows
                if self._should_skip(tx_desc):
                    logger.debug("Skipping non-transaction row: %s", tx_desc)
                    continue

                # Classify transaction type FIRST (needed for zero NAV/units logic)
                tx_type = self._classify_transaction(tx_desc)
                if tx_type is None:
                    logger.warning(
                        "MFCentral parser: Unknown transaction type: %s", tx_desc
                    )
                    continue

                # Parse numeric values
                try:
                    nav_float = float(nav) if nav and str(nav) != "nan" else 0.0
                    units_float = float(units) if units and str(units) != "nan" else 0.0
                except (ValueError, TypeError):
                    nav_float = 0.0
                    units_float = 0.0

                # Skip rows with zero NAV and zero units (usually admin updates)
                # BUT allow DIVIDEND transactions (zero NAV/units, only Amount matters)
                if nav_float == 0 and units_float == 0 and tx_type != "DIVIDEND":
                    logger.debug("Skipping row with zero NAV and units: %s", tx_desc)
                    continue

                # Parse date (format: DD-MMM-YYYY, e.g., "16-MAR-2023")
                transaction_date = self._parse_date(date_str)
                if transaction_date is None:
                    logger.warning(
                        "MFCentral parser: Could not parse date: %s", date_str
                    )
                    continue

                # Parse amount for fees (MFCentral doesn't provide separate fees)
                try:
                    is_valid = amount and str(amount) != "nan"
                    amount_float = float(amount) if is_valid else 0.0
                except (ValueError, TypeError):
                    amount_float = 0.0

                # Create ParsedTransaction
                # Use scheme name as ticker_symbol (matched to AMFI code later)
                # For DIVIDEND: use amount as value (quantity=amount, price=1)
                if tx_type == "DIVIDEND":
                    # Dividends have no NAV/units - the amount is the dividend payout
                    transaction = ParsedTransaction(
                        ticker_symbol=scheme_name,
                        transaction_date=transaction_date,
                        transaction_type=tx_type,
                        quantity=abs(amount_float),  # Dividend amount
                        price_per_unit=1.0,  # Unit price for dividend value
                        fees=0.0,
                    )
                else:
                    transaction = ParsedTransaction(
                        ticker_symbol=scheme_name,
                        transaction_date=transaction_date,
                        transaction_type=tx_type,
                        quantity=abs(units_float),
                        price_per_unit=nav_float,
                        fees=0.0,  # MFCentral doesn't provide fee breakdown
                    )
                transactions.append(transaction)

            except Exception as e:
                logger.error(
                    "MFCentral parser: Error parsing row: %s. Error: %s",
                    row.to_dict() if hasattr(row, "to_dict") else str(row),
                    e,
                )

        logger.info("MFCentral parser: Parsed %d transactions", len(transactions))
        return transactions

    def _classify_transaction(self, tx_desc: str) -> str | None:
        """Classify transaction description into BUY, SELL, or DIVIDEND."""
        for tx_type, patterns in self.TRANSACTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, tx_desc, re.IGNORECASE):
                    return tx_type
        return None

    def _should_skip(self, tx_desc: str) -> bool:
        """Check if transaction description matches skip patterns."""
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, tx_desc, re.IGNORECASE):
                return True
        return False

    def _parse_date(self, date_str: str) -> str | None:
        """Parse date from MFCentral format (DD-MMM-YYYY) to ISO format (YYYY-MM-DD)."""
        try:
            # Handle pandas Timestamp objects
            if hasattr(date_str, "strftime"):
                return date_str.strftime("%Y-%m-%d")

            # Parse string format
            parsed = pd.to_datetime(date_str, format="%d-%b-%Y")
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            try:
                # Try alternative formats
                parsed = pd.to_datetime(date_str, dayfirst=True)
                return parsed.strftime("%Y-%m-%d")
            except Exception:
                return None
