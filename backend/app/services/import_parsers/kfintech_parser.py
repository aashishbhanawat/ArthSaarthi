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

# pdfplumber.utils.exceptions may not be bundled correctly by PyInstaller
# Use a fallback exception class if the module is unavailable
try:
    from pdfplumber.utils.exceptions import PdfminerException
except ImportError:
    # Fallback: catch generic Exception in the parse method
    PdfminerException = Exception

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# Silence pdfminer's extremely verbose debug logging
logging.getLogger("pdfminer").setLevel(logging.WARNING)


class KFintechParser(BaseParser):
    """
    Parser for KFintech PDF statements.

    KFintech serves ~35% of Indian AMCs including SBI, Axis, UTI,
    Nippon India, Mirae Asset, Canara Robeco, and others.
    """

    # Patterns for transaction types
    # Note: PDF extraction sometimes breaks words (e.g., "I DCW", "S IP", "S ystematic")
    TRANSACTION_PATTERNS = {
        "BUY": [
            r"^Purchase",
            r"^P\s*urchase",  # Handle broken "P urchase"
            r"^S\s*IP\s*Purchase",  # Handle "S IP Purchase"
            r"^SIP\s*Purchase",
            r"^Switch\s*-?\s*In",
            r"^S\s*ystematic\s*Investment",  # Handle "S ystematic Investment"
            r"^Systematic\s*Investment",
        ],
        "SELL": [
            r"^Redemption",
            r"^R\s*edemption",  # Handle broken "R edemption"
            r"^\*\s*Redemption",  # Handle "* Redemption Of Units"
            r"^Switch\s*-?\s*Out",
            r"^S\s*witch\s*-?\s*Out",  # Handle "S witch Out"
            r"^S\s*ystematic\s*Withdrawal",  # Handle broken "S ystematic Withdrawal"
            r"^Systematic\s*Withdrawal",
        ],
        "IDCW_REINVEST": [
            r"^I\s*DCW\s*Reinvest",  # Handle "I DCW Reinvestment"
            r"^IDCW\s*Reinvest",
            r"^Dividend\s*Reinvest",
        ],
        "DIVIDEND": [
            r"^I\s*DCW\s*Paid",  # Handle "I DCW Paid"
            r"^I\s*DCW\s*Payout",  # Handle "I DCW Payout"
            r"^IDCW\s*Paid",
            r"^IDCW\s*Payout",
            r"^Dividend\s*Paid",
            r"^\*+\s*IDCW\s*Paid",  # Handle "*** IDCW Paid ***"
            r"^\*\s*\*+\s*IDCW\s*Paid",  # Handle "* ** IDCW Paid ***"
        ],
    }

    # Patterns to skip
    SKIP_PATTERNS = [
        r"^\*\*\*.*Stamp Duty",  # *** Stamp Duty ***
        r"^\*\*\*.*STT",  # *** STT Paid ***
        r"^\*\*\*.*TDS",  # *** TDS Deducted ***
        r"^\*\*\*.*Less,",  # *** Less, TDS deducted ***
        r"^\*\*\*.*Change",  # *** Change of Contact ***
        r"^\*\s*\*+.*Address",  # * ** Address Updated ***
        r"^\*\s*\*+.*Change",  # * ** Change of Contact ***
        r"^\*\s*\*+.*Registration",  # * ** Registration of Nominee ***
        r"^\*\s*\*+.*Regn",  # * ** Change / Regn of Nominee ***
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
        r"^S\s*witch.*Merger",  # S witch Out - Merger
        r"^C\*\*",  # Corrupted text like "C**I*T SINT2T2"
        r"^\s*$",  # Empty lines
    ]

    def __init__(self):
        """Initialize the parser."""
        self.current_scheme = None
        self.current_folio = None
        self.current_isin = None

    def _degarble_line(self, line: str) -> str:
        """
        Fix garbled date patterns from PDF column interleaving.

        PDF extraction sometimes interleaves characters from two dates
        when columns overlap, e.g.:
            '2294--NJaonv--22002221 P urchase' should be '24-Jan-2022 Purchase'

        The interleaving pattern is:
            char1_dateA + char1_dateB + char2_dateA + char2_dateB...
        So to get dateB, we take odd positions (1, 3, 5, 7...)
        """
        # Match pattern: starts with 4 digits, has garbled month/year
        garbled_match = re.match(
            r'^(\d{4})--([A-Za-z]{6,8})--(\d{8})\s+(.+)$', line
        )
        if garbled_match:
            day_garble = garbled_match.group(1)  # e.g., "2294"
            month_garble = garbled_match.group(2)  # e.g., "NJaonv"
            year_garble = garbled_match.group(3)  # e.g., "22002221"
            rest = garbled_match.group(4)

            try:
                # Extract second date (dateB) from odd positions
                day2 = day_garble[1] + day_garble[3]  # positions 1,3 -> "24"

                # Month: odd positions (1,3,5)
                month_range = range(1, min(6, len(month_garble)), 2)
                month2 = ''.join([month_garble[i] for i in month_range])

                # Year: odd positions (1,3,5,7)
                year_range = range(1, min(8, len(year_garble)), 2)
                year2 = ''.join([year_garble[i] for i in year_range])

                # Validate the extracted date components
                if len(day2) == 2 and len(month2) == 3 and len(year2) == 4:
                    clean_date = f"{day2}-{month2}-{year2}"
                    logger.debug(f"De-garbled: {clean_date}")
                    return f"{clean_date} {rest}"
            except (IndexError, ValueError):
                pass

        return line

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
                    # Use standard text extraction - layout mode causes issues
                    text = page.extract_text()
                    if text:
                        page_transactions = self._parse_page_text(text)
                        transactions.extend(page_transactions)

        except (PdfminerException, PDFPasswordIncorrect) as e:
            # PdfminerException wraps PDFPasswordIncorrect but str(e) is empty
            # Check repr or exception args for password indicator
            error_repr = repr(e)
            if (
                "password" in error_repr.lower() or
                isinstance(e, PDFPasswordIncorrect) or
                "PDFPasswordIncorrect" in error_repr
            ):
                raise ValueError("PASSWORD_REQUIRED")
            raise

        logger.info(
            "KFintech parser: Parsed %d transactions", len(transactions)
        )
        return transactions

    def _parse_table(self, table: List[List[str]]) -> List[ParsedTransaction]:
        """Parse a table extracted by pdfplumber.

        Table columns are typically:
        [Date, Transaction_Type, Amount, Units, NAV, Balance]
        """
        transactions = []

        for row in table:
            if not row or len(row) < 4:
                continue

            # Clean row cells
            row = [cell.strip() if cell else "" for cell in row]

            # Check if first cell is a date
            date_str = row[0]
            date_match = re.match(r'^(\d{2}-[A-Za-z]{3}-\d{4})$', date_str)
            if not date_match:
                # Check for ISIN in the row
                for cell in row:
                    if cell and "ISIN:" in cell:
                        isin_match = re.search(r"ISIN:(\S+)", cell)
                        if isin_match:
                            self.current_isin = isin_match.group(1)
                            logger.debug(f"Table ISIN: {self.current_isin}")
                continue

            transaction_date = self._parse_date(date_str)
            if not transaction_date:
                continue

            # Get transaction description from second column
            tx_desc = row[1] if len(row) > 1 else ""
            tx_type = self._classify_transaction(tx_desc)
            if not tx_type:
                continue

            # Parse amounts: Amount, Units, NAV
            try:
                amount = self._parse_number(row[2]) if len(row) > 2 else 0
                units = self._parse_number(row[3]) if len(row) > 3 else 0
                nav = self._parse_number(row[4]) if len(row) > 4 else 0
            except (ValueError, IndexError):
                continue

            # Skip zero-unit transactions (except dividends)
            if abs(units) < 0.001 and tx_type not in ["DIVIDEND"]:
                continue

            # Use ISIN as ticker
            if self.current_isin:
                ticker = f"ISIN:{self.current_isin}"
            else:
                ticker = "Unknown Fund"

            logger.debug(
                f"Table Tx: {transaction_date}, {tx_type}, {units}"
            )

            if tx_type == "IDCW_REINVEST":
                transactions.append(ParsedTransaction(
                    ticker_symbol=ticker,
                    transaction_date=transaction_date,
                    transaction_type="DIVIDEND",
                    quantity=abs(amount),
                    price_per_unit=1.0,
                    fees=0.0,
                ))
                transactions.append(ParsedTransaction(
                    ticker_symbol=ticker,
                    transaction_date=transaction_date,
                    transaction_type="BUY",
                    quantity=abs(units),
                    price_per_unit=nav,
                    fees=0.0,
                ))
            elif tx_type == "DIVIDEND":
                transactions.append(ParsedTransaction(
                    ticker_symbol=ticker,
                    transaction_date=transaction_date,
                    transaction_type="DIVIDEND",
                    quantity=abs(amount),
                    price_per_unit=1.0,
                    fees=0.0,
                ))
            else:
                transactions.append(ParsedTransaction(
                    ticker_symbol=ticker,
                    transaction_date=transaction_date,
                    transaction_type=tx_type,
                    quantity=abs(units),
                    price_per_unit=nav,
                    fees=0.0,
                ))

        return transactions

    def _parse_page_text(self, text: str) -> List[ParsedTransaction]:
        """Parse text from a single page."""
        transactions = []
        lines = text.split("\n")
        previous_line = ""

        for line in lines:
            line = line.strip()

            # NOTE: De-garble disabled - produces wrong dates
            # The garbled lines (e.g., "2294--NJaonv--22002221") will be skipped
            # since they don't match the date regex
            # line = self._degarble_line(line)

            # Check for scheme header (contains ISIN)
            if "ISIN:" in line:
                # Extract ISIN for lookup
                isin_match = re.search(r"ISIN:(\S+)", line)
                isin = isin_match.group(1) if isin_match else None

                # Try to get scheme name from this line
                scheme = self._extract_scheme_name(line)
                logger.debug(f"ISIN line: '{line}' -> scheme: '{scheme}'")

                # If scheme name looks like ISIN: or is empty, use previous line
                if not scheme or scheme.startswith("ISIN:") or len(scheme) < 5:
                    scheme = self._extract_scheme_name(previous_line)
                    logger.debug(
                        f"Using prev line: '{previous_line[:40]}'"
                    )

                # If still no good scheme name, use ISIN as identifier
                if not scheme or scheme.startswith("ISIN:") or len(scheme) < 5:
                    scheme = f"ISIN:{isin}" if isin else "Unknown Fund"
                    logger.debug(f"Fallback to ISIN: {scheme}")

                self.current_scheme = scheme
                self.current_isin = isin
                previous_line = ""
                continue

            # Check for folio header
            folio_match = re.search(r"Folio No\s*:\s*(\S+)", line)
            if folio_match:
                self.current_folio = folio_match.group(1)
                continue

            # Skip non-transaction lines
            if self._should_skip(line):
                previous_line = line
                continue

            # Try to parse as transaction
            tx = self._parse_transaction_line(line)
            if tx:
                if isinstance(tx, list):
                    transactions.extend(tx)
                else:
                    transactions.append(tx)
                previous_line = ""
            else:
                # Save line - might be scheme name for next ISIN line
                previous_line = line

        return transactions

    def _extract_scheme_name(self, line: str) -> str:
        """Extract scheme name from header line.

        KFintech formats:
        - "CODE-Scheme Name (Advisor:XXX) - ISIN:XXX"
        - "Scheme Name - ISIN:XXX"
        - "CODE-Scheme Name (Direct) - ISIN:XXX"
        """
        # Remove ISIN suffix first
        line = re.sub(r"\s*-?\s*ISIN:\S+", "", line)

        # Remove Advisor info
        line = re.sub(r"\s*\(Advisor[^)]*\)", "", line)

        # Try to extract scheme name after CODE- prefix
        match = re.match(r"^\S+-(.+)$", line.strip())
        if match:
            scheme = match.group(1).strip()
            if scheme and len(scheme) > 3:
                return scheme

        # Fallback: use the cleaned line
        cleaned = line.strip()
        if cleaned and len(cleaned) > 3:
            return cleaned

        return "Unknown Fund"

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
        # Handle double-date lines: "29-Nov-2021 24-Jan-2022 Purchase ..."
        # where PDF extraction merges lines incorrectly
        date_match = re.match(r"^(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+)$", line)
        if not date_match:
            return None

        date_str = date_match.group(1)
        rest = date_match.group(2)

        # Check if rest starts with another date (double-date line)
        second_date_match = re.match(r"^(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+)$", rest)
        if second_date_match:
            # Use the second date as the actual transaction date
            date_str = second_date_match.group(1)
            rest = second_date_match.group(2)

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
            # Check if part is numeric (handles commas, negative, and parentheses)
            # Parentheses like (1,00,000.00) indicate negative/sold values
            clean = part.replace(",", "").replace("-", "")
            clean = clean.replace("(", "").replace(")", "")
            if re.match(r"^\d+\.?\d*$", clean) and len(numeric_parts) > 0:
                numeric_parts.append(part)
            elif re.match(r"^[\(\)-]?\d+[\d,\.]*\)?$", part.replace(",", "")):
                numeric_parts.append(part)
            else:
                if not numeric_parts:  # Only add to desc before numerics
                    tx_desc_parts.append(part)

        tx_desc = " ".join(tx_desc_parts)
        tx_type = self._classify_transaction(tx_desc)

        # Debug logging for transaction classification
        logger.debug(f"Transaction: date={date_str}, desc='{tx_desc}', type={tx_type}")

        if not tx_type:
            return None

        # Parse numeric values: AMOUNT, UNITS, NAV, BALANCE
        # KFintech PDF columns: Amount | Units | Price (NAV) | Balance
        # Note: descriptions like "Systematic Instalment No 1" have the "1"
        # parsed as first numeric, skipping small integers (instalment numbers)
        try:
            # Skip small integers at the start (likely instalment numbers)
            start_idx = 0
            while start_idx < len(numeric_parts) - 3:  # Need at least 3 parts after
                first_val = self._parse_number(numeric_parts[start_idx])
                # If first value is a small integer (1-100), likely an instalment number
                if first_val == int(first_val) and 1 <= first_val <= 100:
                    start_idx += 1
                else:
                    break

            n = len(numeric_parts)
            i = start_idx
            amount = self._parse_number(numeric_parts[i]) if n > i else 0
            units = self._parse_number(numeric_parts[i + 1]) if n > i + 1 else 0
            nav = self._parse_number(numeric_parts[i + 2]) if n > i + 2 else 0

            # Debug: log numeric parts for troubleshooting
            logger.debug(
                f"  Nums: {numeric_parts[:4]} idx={start_idx} "
                f"amt={amount} units={units} nav={nav}"
            )
        except (ValueError, IndexError):
            return None

        # Validation: for BUY/SELL, check that units × NAV ≈ amount (within 5%)
        # This catches cases where amount is incorrectly parsed as units
        if tx_type in ["BUY", "SELL"] and amount > 0 and units > 0 and nav > 0:
            calculated_amount = units * nav
            if abs(calculated_amount - amount) / amount > 0.05:
                # Calculated amount doesn't match - values might be swapped
                # Skip if calculated amount is way off (likely parsing error)
                if abs(calculated_amount - amount) / amount > 0.5:
                    logger.debug(
                        f"  Skipping: units×NAV={calculated_amount:.2f} "
                        f"!= amt={amount:.2f}"
                    )
                    return None

        # Skip zero-unit transactions (except dividends paid out)
        if abs(units) < 0.001 and tx_type not in ["DIVIDEND"]:
            return None

        # Use ISIN as primary ticker (for auto-matching), fallback to scheme name
        if self.current_isin:
            ticker = f"ISIN:{self.current_isin}"
        elif self.current_scheme and self.current_scheme != "Unknown Fund":
            ticker = self.current_scheme
        else:
            ticker = "Unknown Fund"

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
        """Parse number string, handling commas and parentheses."""
        if not num_str:
            return 0.0
        # Remove commas and parentheses
        clean = num_str.replace(",", "").replace("(", "").replace(")", "")
        return float(clean)
