"""KFintech XLS Transaction Statement Parser.

Parses KFintech transaction statement files in XLSX format.
This is the recommended import method for KFintech as it provides
clean structured data without the garbling issues of PDF extraction.

Download from: mfs.kfintech.com → Transaction Statement → Excel format
"""
import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class KFintechXlsParser(BaseParser):
    """Parser for KFintech XLS transaction statements."""

    # Expected columns in KFintech XLS
    EXPECTED_COLUMNS = [
        'FundName',
        'Scheme Description',
        'Transaction Date',
        'Transaction Description',
        'Amount',
        'Units',
        'NAV',
        'SchemeISIN',
    ]

    # Transaction type mapping
    TRANSACTION_MAP = {
        'Purchase': 'BUY',
        'Purchase Online': 'BUY',
        'Purchase Physical': 'BUY',
        'Redemption': 'SELL',
        'Switch In': 'BUY',
        'Switch Out': 'SELL',
        'SIP Purchase': 'BUY',
        'Systematic Investment': 'BUY',
        'IDCW Reinvestment': 'DIVIDEND',
        'Dividend Reinvestment': 'DIVIDEND',
    }

    # Patterns to skip (non-transaction rows)
    SKIP_PATTERNS = [
        'Address updated',
        'Bank Mandate',
        'Nomination',
        'KYC',
        'Folio',
    ]

    def parse(
        self, file_path: str, password: Optional[str] = None
    ) -> List[ParsedTransaction]:
        """
        Parse KFintech XLS file into ParsedTransaction objects.

        Args:
            file_path: Path to the XLS/XLSX file
            password: Not used for XLS files

        Returns:
            List of ParsedTransaction objects
        """
        transactions = []

        try:
            # Try openpyxl first (for .xlsx), fall back to xlrd (for .xls)
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
            except Exception:
                df = pd.read_excel(file_path, engine='xlrd')

            logger.info(f"KFintech XLS: Loaded {len(df)} rows")

            # Validate columns
            missing_cols = []
            for col in self.EXPECTED_COLUMNS:
                if col not in df.columns:
                    missing_cols.append(col)

            if missing_cols:
                logger.warning(f"Missing columns: {missing_cols}")

            # Process each row
            for idx, row in df.iterrows():
                tx = self._parse_row(row, idx)
                if tx:
                    transactions.append(tx)

        except Exception as e:
            logger.error(f"Failed to parse KFintech XLS: {e}")
            raise

        logger.info(f"KFintech XLS parser: Parsed {len(transactions)} tx")
        return transactions

    def _parse_row(self, row: pd.Series, idx: int) -> Optional[ParsedTransaction]:
        """Parse a single row into a ParsedTransaction."""
        try:
            # Get transaction description
            tx_desc = str(row.get('Transaction Description', '')).strip()

            # Skip non-transaction rows
            if self._should_skip(tx_desc):
                logger.debug(f"Row {idx}: Skipping '{tx_desc}'")
                return None

            # Classify transaction type
            tx_type = self._classify_transaction(tx_desc)
            if not tx_type:
                # Check if negative amount indicates SELL
                amount = row.get('Amount', 0)
                if pd.notna(amount) and float(amount) < 0:
                    tx_type = 'SELL'
                else:
                    logger.debug(f"Row {idx}: Unknown tx type '{tx_desc}'")
                    return None

            # Parse date
            date_val = row.get('Transaction Date')
            transaction_date = self._parse_date(date_val)
            if not transaction_date:
                logger.warning(f"Row {idx}: Invalid date '{date_val}'")
                return None

            # Get ISIN as ticker (for auto-matching)
            isin = str(row.get('SchemeISIN', '')).strip()
            if isin and len(isin) == 12:
                ticker_symbol = f"ISIN:{isin}"
            else:
                # Fallback to Product Code
                ticker_symbol = str(row.get('Product Code', 'Unknown'))

            # Get numeric values
            amount = abs(float(row.get('Amount', 0) or 0))
            units = abs(float(row.get('Units', 0) or 0))
            nav = float(row.get('NAV', 0) or 0)

            # Skip zero-unit transactions (except dividends)
            if units < 0.001 and tx_type not in ['DIVIDEND']:
                logger.debug(f"Row {idx}: Skipping zero-unit transaction")
                return None

            # Create transaction
            return ParsedTransaction(
                ticker_symbol=ticker_symbol,
                transaction_date=transaction_date,
                transaction_type=tx_type,
                quantity=units,
                price_per_unit=nav,
                fees=0.0,
            )

        except Exception as e:
            logger.warning(f"Row {idx}: Parse error - {e}")
            return None

    def _should_skip(self, tx_desc: str) -> bool:
        """Check if transaction should be skipped."""
        tx_lower = tx_desc.lower()
        for pattern in self.SKIP_PATTERNS:
            if pattern.lower() in tx_lower:
                return True
        # Skip rows starting with ***
        if tx_desc.startswith('***'):
            return True
        return False

    def _classify_transaction(self, tx_desc: str) -> Optional[str]:
        """Classify transaction description to internal type."""
        tx_lower = tx_desc.lower()

        for pattern, tx_type in self.TRANSACTION_MAP.items():
            if pattern.lower() in tx_lower:
                return tx_type

        return None

    def _parse_date(self, date_val) -> Optional[str]:
        """Parse date value to YYYY-MM-DD format."""
        if pd.isna(date_val):
            return None

        # If already a datetime
        if isinstance(date_val, datetime):
            return date_val.strftime('%Y-%m-%d')

        # Try parsing string date
        date_str = str(date_val).strip()
        for fmt in ['%d-%b-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None
