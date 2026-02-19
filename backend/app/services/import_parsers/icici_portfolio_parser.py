
import logging
from typing import List

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser


class IciciPortfolioParser(BaseParser):
    """
    Parser for ICICI Direct Portfolio Equity All (CSV/Excel) files.
    Columns: Stock Symbol, Company Name, ISIN Code, Action, Quantity,
             Transaction Price, Brokerage, Transaction Charges, StampDuty,
             Segment, STT Paid/Not Paid, Remarks, Transaction Date, Exchange
    """

    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parses ICICI Portfolio DataFrame.
        Returns a list of ParsedTransaction objects.
        """
        transactions = []

        # Define expected columns and map them to our schema
        column_map = {
            "Transaction Date": "transaction_date",
            "Stock Symbol": "ticker_symbol",
            "Action": "transaction_type",
            "Quantity": "quantity",
            "Transaction Price": "price_per_unit",
            "ISIN Code": "isin",
        }

        # Columns to be summed up for fees
        fee_columns = [
            "Brokerage",
            "Transaction Charges",
            "StampDuty",
        ]

        # Normalize column names (strip whitespace)
        df.columns = df.columns.str.strip()

        required_columns = list(column_map.keys())

        # Check if all required columns exist
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logging.error(
                "ICICI Portfolio parser: Missing required columns: %s",
                missing_cols,
            )
            return []

        # Rename core columns
        df_renamed = df.rename(columns=column_map)

        # Calculate total fees
        # Ensure fee columns are numeric, coercing errors to 0
        for col in fee_columns:
            if col in df_renamed.columns:
                df_renamed[col] = pd.to_numeric(
                    df_renamed[col], errors="coerce"
                ).fillna(0)
            else:
                df_renamed[col] = 0

        df_renamed["fees"] = df_renamed[fee_columns].sum(axis=1)

        # Filter for valid actions
        # Action column might be mixed case
        if "transaction_type" in df_renamed.columns:
            df_renamed["transaction_type"] = (
                df_renamed["transaction_type"].astype(str).str.upper().str.strip()
            )

        valid_actions = ["BUY", "SELL"]
        df_trades = df_renamed[
            df_renamed["transaction_type"].isin(valid_actions)
        ].copy()

        # Convert date format
        # Format in sample: 08-Jul-2015
        try:
            df_trades["transaction_date"] = pd.to_datetime(
                df_trades["transaction_date"], format="%d-%b-%Y", errors='coerce'
            )
            # Drop invalid dates
            df_trades = df_trades.dropna(subset=["transaction_date"])
            df_trades["transaction_date"] = df_trades[
                "transaction_date"
            ].dt.strftime("%Y-%m-%d")
        except Exception as e:
            logging.error(f"ICICI Portfolio parser: Date parsing error: {e}")
            return []

        for _, row in df_trades.iterrows():
            try:
                # Handle numeric fields
                qty = pd.to_numeric(row.get("quantity"), errors='coerce') or 0
                price = pd.to_numeric(row.get("price_per_unit"), errors='coerce') or 0
                fees = pd.to_numeric(row.get("fees"), errors='coerce') or 0

                ticker = str(row.get("ticker_symbol", "")).strip()
                isin = str(row.get("isin", "")).strip()

                if qty <= 0:
                    continue

                transactions.append(ParsedTransaction(
                    ticker_symbol=ticker,
                    transaction_date=row["transaction_date"],
                    transaction_type=row["transaction_type"],
                    quantity=float(qty),
                    price_per_unit=float(price),
                    fees=float(fees),
                    isin=isin if isin else None
                ))
            except Exception as e:
                logging.error(
                    f"ICICI Portfolio parser: Error parsing row. Error: {e}"
                )

        return transactions
