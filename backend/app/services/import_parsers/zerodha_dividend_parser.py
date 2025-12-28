"""Zerodha Dividend Statement Parser.

Parses dividend statements from Zerodha (XLSX format).
"""
import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class ZerodhaDividendParser(BaseParser):
    """Parser for Zerodha Dividend Statement XLSX files."""

    # Required columns (lowercase, underscored)
    REQUIRED_COLUMNS = ['isin', 'ex-date', 'quantity', 'dividend_per_share']

    def parse(
        self, df: pd.DataFrame, password: Optional[str] = None
    ) -> List[ParsedTransaction]:
        """
        Parse Zerodha dividend statement DataFrame.

        Args:
            df: DataFrame with dividend data (already skiprows applied)
            password: Not used for XLSX

        Returns:
            List of ParsedTransaction objects
        """
        transactions = []

        # Normalize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        logger.info(f"Zerodha Dividend parser: Columns: {df.columns.tolist()}")

        # Check required columns
        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            logger.error(f"Zerodha Dividend parser: Missing columns: {missing}")
            raise ValueError(f"Missing required columns: {missing}")

        for idx, row in df.iterrows():
            try:
                tx = self._parse_row(row, idx)
                if tx:
                    transactions.append(tx)
            except Exception as e:
                logger.warning(f"Row {idx}: Failed to parse - {e}")
                continue

        logger.info(
            f"Zerodha Dividend parser: Parsed {len(transactions)} transactions"
        )
        return transactions

    def _parse_row(
        self, row: pd.Series, idx: int
    ) -> Optional[ParsedTransaction]:
        """Parse a single row into a transaction."""
        # Extract ISIN
        isin = str(row.get('isin', '')).strip()
        if not isin or isin == 'nan':
            return None

        # Use ISIN format for ticker
        ticker_symbol = f"ISIN:{isin}"

        # Parse date (ex-date)
        ex_date = row.get('ex-date')
        transaction_date = self._parse_date(ex_date)
        if not transaction_date:
            logger.debug(f"Row {idx}: Invalid date: {ex_date}")
            return None

        # Parse quantity
        quantity = self._parse_number(row.get('quantity'))
        if quantity is None or quantity <= 0:
            return None

        # Parse dividend per share
        dividend_per_share = self._parse_number(row.get('dividend_per_share'))
        if dividend_per_share is None or dividend_per_share <= 0:
            return None

        return ParsedTransaction(
            ticker_symbol=ticker_symbol,
            transaction_date=transaction_date,
            transaction_type="DIVIDEND",
            quantity=quantity,
            price_per_unit=dividend_per_share,
            fees=0.0,
        )

    def _parse_date(self, value) -> Optional[str]:
        """Parse date to YYYY-MM-DD format."""
        if pd.isna(value):
            return None

        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')

        if isinstance(value, str):
            # Try multiple formats
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(value, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue

        return None

    def _parse_number(self, value) -> Optional[float]:
        """Parse numeric value."""
        if pd.isna(value):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            # Remove commas and parse
            try:
                return float(value.replace(',', ''))
            except ValueError:
                return None

        return None
