"""
KFintech PDF Parser.

Parses Mutual Fund statements from KFintech (formerly Karvy).
Handles password-protected PDFs and multi-section format.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfplumber.utils.exceptions import PdfminerException

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class KFintechParser(BaseParser):
    """
    Parser for KFintech PDF statements.

    KFintech serves ~35% of Indian AMCs including SBI, Axis, UTI,
    Nippon India, Mirae Asset, Canara Robeco, and others.
    """

    # Patterns for transaction types
    TRANSACTION_PATTERNS = {
        "BUY": [
            r"^Purchase",
            r"^SIP Purchase",
            r"^Switch\s*In",
            r"^Systematic Investment",
        ],
        "SELL": [
            r"^Redemption",
            r"^Switch\s*Out",
            r"^Systematic Withdrawal",
        ],
        "IDCW_REINVEST": [
            r"^IDCW Reinvestment",
            r"^Dividend Reinvest",
        ],
        "DIVIDEND": [
            r"^IDCW Payout",
            r"^Dividend Paid",
        ],
    }

    # Patterns to skip
    SKIP_PATTERNS = [
        r"^\*\*\*",  # *** Stamp Duty ***, *** TDS Deducted ***
        r"^Opening Unit Balance",
        r"^Closing Unit Balance",
        r"^Entry Load",
        r"^Exit Load",
        r"^Folio No",
        r"^PAN:",
        r"^KYC",
        r"^Nominee",
        r"^Registrar",
        r"^ISIN:",
        r"^Advisor:",
        r"^Switch.*Merger",  # TODO: Handle Switch In/Out - Merger later
        r"^\s*$",  # Empty lines
    ]

    def __init__(self):
        """Initialize the parser."""
        self.current_scheme = None
        self.current_folio = None

    def parse(
        self, file_path: str, password: Optional[str] = None
    ) -> List[ParsedTransaction]:
        """
        Parse KFintech PDF into ParsedTransaction objects.

        Args:
            file_path: Path to the PDF file
            password: Optional password for protected PDFs

        Returns:
            List of ParsedTransaction objects

        Raises:
            ValueError: If password is required but not provided
        """
        transactions = []

        try:
            with pdfplumber.open(file_path, password=password or "") as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        page_transactions = self._parse_page_text(text)
                        transactions.extend(page_transactions)

        except (PdfminerException, PDFPasswordIncorrect) as e:
            if "password" in str(e).lower() or isinstance(e, PDFPasswordIncorrect):
                raise ValueError("PASSWORD_REQUIRED")
            raise

        logger.info(
            "KFintech parser: Parsed %d transactions", len(transactions)
        )
        return transactions

    def _parse_page_text(self, text: str) -> List[ParsedTransaction]:
        """Parse text from a single page."""
        transactions = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            # Check for scheme header (contains ISIN)
            if "ISIN:" in line:
                self.current_scheme = self._extract_scheme_name(line)
                continue

            # Check for folio header
            folio_match = re.search(r"Folio No\s*:\s*(\S+)", line)
            if folio_match:
                self.current_folio = folio_match.group(1)
                continue

            # Skip non-transaction lines
            if self._should_skip(line):
                continue

            # Try to parse as transaction
            tx = self._parse_transaction_line(line)
            if tx:
                if isinstance(tx, list):
                    transactions.extend(tx)
                else:
                    transactions.append(tx)

        return transactions

    def _extract_scheme_name(self, line: str) -> str:
        """Extract scheme name from header line."""
        # Line format: CODE-Scheme Name (Advisor:XXX) - ISIN:XXX
        # Try to extract the scheme name before (Advisor
        match = re.search(r"^\S+-(.+?)\s*\(Advisor", line)
        if match:
            return match.group(1).strip()

        # Fallback: everything before ISIN
        match = re.search(r"^(.+?)\s*-\s*ISIN:", line)
        if match:
            return match.group(1).strip()

        return line[:50]  # Fallback to first 50 chars

    def _should_skip(self, line: str) -> bool:
        """Check if line should be skipped."""
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        return False

    def _classify_transaction(self, tx_desc: str) -> Optional[str]:
        """Classify transaction description."""
        for tx_type, patterns in self.TRANSACTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, tx_desc, re.IGNORECASE):
                    return tx_type
        return None

    def _parse_transaction_line(
        self, line: str
    ) -> Optional[List[ParsedTransaction] | ParsedTransaction]:
        """
        Parse a transaction line.

        KFintech format:
        DD-MMM-YYYY Transaction_Type AMOUNT UNITS NAV BALANCE
        """
        # Match date at the start: DD-MMM-YYYY
        date_match = re.match(r"^(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+)$", line)
        if not date_match:
            return None

        date_str = date_match.group(1)
        rest = date_match.group(2)

        # Parse the date
        transaction_date = self._parse_date(date_str)
        if not transaction_date:
            return None

        # Extract transaction type and amounts
        # Pattern: Transaction_Type AMOUNT UNITS NAV BALANCE
        # Note: numbers may have commas and be negative
        parts = re.split(r"\s+", rest)

        if len(parts) < 2:
            return None

        # Build transaction description from non-numeric leading parts
        tx_desc_parts = []
        numeric_parts = []

        for part in parts:
            # Check if part is numeric (handles commas and negative)
            clean = part.replace(",", "").replace("-", "")
            if re.match(r"^\d+\.?\d*$", clean) and len(numeric_parts) > 0:
                numeric_parts.append(part)
            elif re.match(r"^-?\d+[\d,\.]*$", part.replace(",", "")):
                numeric_parts.append(part)
            else:
                if not numeric_parts:  # Only add to desc before numerics
                    tx_desc_parts.append(part)

        tx_desc = " ".join(tx_desc_parts)
        tx_type = self._classify_transaction(tx_desc)

        if not tx_type:
            return None

        # Parse numeric values: AMOUNT, UNITS, NAV, BALANCE
        try:
            amount = self._parse_number(numeric_parts[0]) if numeric_parts else 0
            units = self._parse_number(numeric_parts[1]) if len(numeric_parts) > 1 else 0
            nav = self._parse_number(numeric_parts[2]) if len(numeric_parts) > 2 else 0
        except (ValueError, IndexError):
            return None

        # Skip zero-unit transactions (except dividends paid out)
        if abs(units) < 0.001 and tx_type not in ["DIVIDEND"]:
            return None

        ticker = self.current_scheme or "Unknown Fund"

        # Handle IDCW Reinvestment as 2 transactions
        if tx_type == "IDCW_REINVEST":
            dividend_tx = ParsedTransaction(
                ticker_symbol=ticker,
                transaction_date=transaction_date,
                transaction_type="DIVIDEND",
                quantity=abs(amount),
                price_per_unit=1.0,
                fees=0.0,
            )
            buy_tx = ParsedTransaction(
                ticker_symbol=ticker,
                transaction_date=transaction_date,
                transaction_type="BUY",
                quantity=abs(units),
                price_per_unit=nav,
                fees=0.0,
            )
            return [dividend_tx, buy_tx]

        # Map to final type
        final_type = tx_type
        if tx_type == "DIVIDEND":
            return ParsedTransaction(
                ticker_symbol=ticker,
                transaction_date=transaction_date,
                transaction_type="DIVIDEND",
                quantity=abs(amount),
                price_per_unit=1.0,
                fees=0.0,
            )

        return ParsedTransaction(
            ticker_symbol=ticker,
            transaction_date=transaction_date,
            transaction_type=final_type,
            quantity=abs(units),
            price_per_unit=nav,
            fees=0.0,
        )

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date from DD-MMM-YYYY format."""
        try:
            parsed = datetime.strptime(date_str, "%d-%b-%Y")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            return None

    def _parse_number(self, num_str: str) -> float:
        """Parse number string, handling commas."""
        if not num_str:
            return 0.0
        clean = num_str.replace(",", "")
        return float(clean)
