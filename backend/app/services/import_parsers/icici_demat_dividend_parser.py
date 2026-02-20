"""ICICI DEMAT Dividend Statement Parser.

Parses dividend information from ICICI DEMAT Account Statement PDFs.
Extracts dividends from the "Corporate Benefits" section.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class IciciDematDividendParser(BaseParser):
    """Parser for ICICI DEMAT Account Statement PDF dividend section."""

    # Date pattern for record/payment dates (DD-Mon-YYYY or DD-MMM-YYYY)
    DATE_PATTERN = re.compile(r'(\d{1,2}-[A-Za-z]{3}-\d{4})')

    # ISIN pattern (12 characters starting with INE)
    ISIN_PATTERN = re.compile(r'(INE[A-Z0-9]{9})')

    # Numeric values with optional decimals, not preceded by a capital letter
    NUMBER_PATTERN = re.compile(r'(?<![A-Z])(\d+(?:\.\d+)?)')

    def parse(
        self, file_path: str, password: Optional[str] = None
    ) -> List[ParsedTransaction]:
        """
        Parse ICICI DEMAT statement PDF for dividend transactions.

        Args:
            file_path: Path to the PDF file
            password: Optional password for protected PDFs

        Returns:
            List of ParsedTransaction objects (DIVIDEND type)
        """
        transactions = []

        try:
            with pdfplumber.open(file_path, password=password) as pdf:
                logger.info(
                    f"ICICI DEMAT Dividend parser: Processing {len(pdf.pages)} pages"
                )

                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text:
                        continue

                    # Only parse pages with Corporate Benefits section
                    if 'Corporate Benefits' in text:
                        page_txs = self._parse_corporate_benefits(
                            text, page_num
                        )
                        transactions.extend(page_txs)

        except PDFPasswordIncorrect:
            logger.warning("ICICI DEMAT parser: PDF is password protected")
            raise ValueError("PASSWORD_REQUIRED")
        except PDFSyntaxError as e:
            logger.error(f"ICICI DEMAT parser: PDF syntax error - {e}")
            raise
        except Exception as e:
            logger.error(f"ICICI DEMAT parser: Error - {e}")
            raise

        logger.info(
            f"ICICI DEMAT Dividend parser: Parsed {len(transactions)} transactions"
        )
        return transactions

    def _parse_corporate_benefits(
        self, text: str, page_num: int
    ) -> List[ParsedTransaction]:
        """Parse Corporate Benefits section for dividend entries."""
        transactions = []

        # Find the Corporate Benefits section
        lines = text.split('\n')
        in_benefits_section = False

        for line in lines:
            # Start of Corporate Benefits section
            if 'Corporate Benefits for record date' in line:
                in_benefits_section = True
                continue

            # Stop at expected/future dividends or disclaimers
            if in_benefits_section:
                if 'expected between' in line.lower():
                    break
                if 'disclaimer' in line.lower():
                    break
                if 'calculated assuming' in line.lower():
                    break

            if not in_benefits_section:
                continue

            # Try to parse dividend line
            tx = self._parse_dividend_line(line, page_num)
            if tx:
                transactions.append(tx)

        return transactions

    def _parse_dividend_line(
        self, line: str, page_num: int
    ) -> Optional[ParsedTransaction]:
        """Parse a single dividend line containing ISIN + date + values."""
        # Don't require 'dividend' keyword - it's on separate line in PDF
        # Instead look for lines with ISIN + date + numeric values

        # Extract ISIN
        isin_match = self.ISIN_PATTERN.search(line)
        if not isin_match:
            return None

        isin = isin_match.group(1)
        ticker_symbol = f"ISIN:{isin}"

        # Extract dates
        dates = self.DATE_PATTERN.findall(line)
        if not dates:
            return None

        # First date is usually Record Date
        record_date = self._parse_date(dates[0])
        if not record_date:
            return None

        # Clean line for number extraction - remove ISIN and date patterns
        clean_line = self.ISIN_PATTERN.sub('', line)
        clean_line = self.DATE_PATTERN.sub('', clean_line)

        # Extract numeric values from cleaned line
        numbers = self._extract_numbers(clean_line)
        if len(numbers) < 2:
            logger.debug(f"Page {page_num}: Not enough numbers in: {line[:60]}")
            return None

        # In ICICI format, numbers are: [units, various_ratios..., value]
        # Example: 40 10 (% ratio) .1 (per unit) 27-Aug-2014 (date) 4 (value)
        # We need: units (first), value (last)
        units = numbers[0]
        value = numbers[-1]

        # Validate
        if units <= 0 or value <= 0:
            return None

        # Calculate dividend per share
        dividend_per_share = value / units if units > 0 else 0

        if dividend_per_share <= 0:
            return None

        logger.debug(
            f"Page {page_num}: {isin} - {units} units, value={value}, "
            f"per_share={dividend_per_share:.4f}"
        )

        return ParsedTransaction(
            ticker_symbol=ticker_symbol,
            transaction_date=record_date,
            transaction_type="DIVIDEND",
            quantity=units,
            price_per_unit=dividend_per_share,
            fees=0.0,
        )

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format."""
        try:
            dt = datetime.strptime(date_str, '%d-%b-%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return None

    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numeric values from text."""
        # Match numbers with optional decimals
        matches = self.NUMBER_PATTERN.findall(text)

        numbers = []
        for match in matches:
            try:
                value = float(match)
                # Skip years (1900-2100) and very small values
                if 1900 <= value <= 2100:
                    continue
                numbers.append(value)
            except ValueError:
                continue

        return numbers
