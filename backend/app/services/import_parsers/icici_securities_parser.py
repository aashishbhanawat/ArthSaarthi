"""ICICI Securities MF Statement Parser.

Parses Mutual Fund Account Statements from ICICI Securities (AMFI ARN-0845).
These are broker statements that contain MF transactions across multiple AMCs.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class ICICISecuritiesParser(BaseParser):
    """Parser for ICICI Securities MF Statement PDF files."""

    # Transaction type mapping
    TRANSACTION_MAP = {
        'purchase': 'BUY',
        'sip': 'BUY',
        'switch in': 'BUY',
        'systematic investment': 'BUY',
        'redemption': 'SELL',
        'switch out': 'SELL',
        'sale': 'SELL',
        'sold': 'SELL',
        'sgb sell': 'SELL',
        'dividend': 'DIVIDEND',
        'idcw': 'DIVIDEND',
    }

    # Patterns to skip
    SKIP_PATTERNS = [
        'opening balance',
        'current unit balance',
        'closing balance',
        'page ',
        'mutual fund account statement',
    ]

    # Date pattern: DD-MMM-YYYY (e.g., 27-Oct-2023)
    DATE_PATTERN = re.compile(r'(\d{1,2}-[A-Za-z]{3}-\d{4})')

    # Transaction line pattern: starts with date, followed by transaction no
    TX_LINE_PATTERN = re.compile(
        r'^(\d{1,2}-[A-Za-z]{3}-\d{4})\s+(\d+)\s+(\w+)'
    )

    # Number pattern: match numbers with optional commas and decimals
    # Handle negative numbers
    NUMBER_PATTERN = re.compile(r'-?[\d,]+\.?\d*')

    def parse(
        self, file_path: str, password: Optional[str] = None
    ) -> List[ParsedTransaction]:
        """
        Parse ICICI Securities MF statement PDF.

        Args:
            file_path: Path to the PDF file
            password: Optional password for protected PDFs

        Returns:
            List of ParsedTransaction objects
        """
        transactions = []
        current_scheme = None

        import pdfplumber
        from pdfminer.pdfdocument import PDFPasswordIncorrect
        from pdfminer.pdfparser import PDFSyntaxError

        try:
            with pdfplumber.open(file_path, password=password) as pdf:
                logger.info(
                    f"ICICI Securities parser: Processing {len(pdf.pages)} pages"
                )

                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text:
                        continue

                    page_transactions, current_scheme = self._parse_page_text(
                        text, current_scheme, page_num
                    )
                    transactions.extend(page_transactions)

        except PDFPasswordIncorrect:
            logger.warning("ICICI parser: PDF is password protected")
            raise ValueError("PASSWORD_REQUIRED")
        except PDFSyntaxError as e:
            logger.error(f"ICICI parser: PDF syntax error - {e}")
            raise
        except Exception as e:
            logger.error(f"ICICI parser: Error - {e}")
            raise

        logger.info(
            f"ICICI Securities parser: Parsed {len(transactions)} transactions"
        )
        return transactions

    def _parse_page_text(
        self, text: str, current_scheme: Optional[str], page_num: int
    ) -> Tuple[List[ParsedTransaction], Optional[str]]:
        """Parse a single page of text."""
        transactions = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for scheme header (contains fund name)
            scheme = self._extract_scheme_name(line)
            if scheme:
                current_scheme = scheme
                logger.debug(f"Page {page_num}: Found scheme: {scheme}")
                continue

            # Skip non-transaction lines
            if self._should_skip(line):
                continue

            # Try to parse as transaction line
            tx = self._parse_transaction_line(line, current_scheme)
            if tx:
                transactions.append(tx)

        return transactions, current_scheme

    def _extract_scheme_name(self, line: str) -> Optional[str]:
        """Extract scheme name from header lines."""
        # Scheme headers typically don't start with a date
        # and contain fund keywords
        line_lower = line.lower()

        # Skip if it looks like a transaction (starts with date)
        if self.DATE_PATTERN.match(line):
            return None

        # Check for fund-related keywords
        fund_keywords = [
            'fund', 'plan', 'growth', 'idcw', 'direct',
            'regular', 'option', 'scheme'
        ]

        has_fund_keyword = any(kw in line_lower for kw in fund_keywords)

        if has_fund_keyword and len(line) > 20:
            # Clean up the scheme name
            # Remove "Folio No:" and everything before scheme name
            if 'folio no' in line_lower:
                return None  # This is AMC header, not scheme

            # Remove common prefixes/suffixes
            scheme = line.strip()
            # Remove leading alphanumeric codes like "DSP" or page info
            if not scheme[0].isalpha():
                return None

            return scheme

        return None

    def _should_skip(self, line: str) -> bool:
        """Check if line should be skipped."""
        line_lower = line.lower()
        for pattern in self.SKIP_PATTERNS:
            if pattern in line_lower:
                return True
        return False

    def _parse_transaction_line(
        self, line: str, current_scheme: Optional[str]
    ) -> Optional[ParsedTransaction]:
        """Parse a transaction line."""
        if not current_scheme:
            return None

        # Match date at start of line
        date_match = self.DATE_PATTERN.match(line)
        if not date_match:
            return None

        date_str = date_match.group(1)

        # Parse the rest of the line
        rest = line[date_match.end():].strip()

        # Extract transaction type
        tx_type = self._classify_transaction(rest)
        if not tx_type:
            return None

        # Extract numeric values (price, units, amount)
        numbers = self._extract_numbers(rest)
        # Format: TxNo, Price, Units, GrossAmt, TDS, STT, NetAmt
        # We need at least 4 numbers (txno, price, units, amount)
        if len(numbers) < 4:
            logger.debug(f"Not enough numbers in: {line[:50]}")
            return None

        # For ICICI format: Transaction No, Type, Price, Units, Amount...
        # Skip transaction number (index 0), use:
        # - numbers[1] = price (NAV)
        # - numbers[2] = units
        # - numbers[3] = gross amount
        try:
            price = numbers[1]
            units = numbers[2]
            amount = numbers[3]

            # Skip if values don't make sense
            if units <= 0 or price <= 0:
                return None

            # Validate: units * price should roughly equal amount
            expected = units * price
            if amount > 0 and abs(expected - amount) / amount > 0.1:
                logger.debug(
                    f"Amount mismatch: {units} * {price} = {expected} "
                    f"!= {amount}"
                )

            # Parse date
            transaction_date = self._parse_date(date_str)
            if not transaction_date:
                return None

            return ParsedTransaction(
                ticker_symbol=current_scheme,
                transaction_date=transaction_date,
                transaction_type=tx_type,
                quantity=abs(units),
                price_per_unit=price,
                fees=0.0,
            )

        except (IndexError, ValueError) as e:
            logger.debug(f"Parse error for line: {line[:50]} - {e}")
            return None

    def _classify_transaction(self, text: str) -> Optional[str]:
        """Classify transaction type from text."""
        text_lower = text.lower()

        for pattern, tx_type in self.TRANSACTION_MAP.items():
            if pattern in text_lower:
                return tx_type

        return None

    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numeric values from text."""
        # Match numbers with optional commas and decimals
        # Handle negative numbers and remove commas
        matches = self.NUMBER_PATTERN.findall(text)

        numbers = []
        for match in matches:
            try:
                # Remove commas and convert
                value = float(match.replace(',', ''))
                numbers.append(value)
            except ValueError:
                continue

        return numbers

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format."""
        try:
            # DD-MMM-YYYY format
            dt = datetime.strptime(date_str, '%d-%b-%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return None
