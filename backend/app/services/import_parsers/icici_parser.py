import logging
from typing import List

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser


class IciciParser(BaseParser):
    """
    Parser for ICICI Direct Tradebook CSV files.
    Assumes a specific format based on user-provided sample.
    """

    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parses an ICICI Direct Tradebook DataFrame and returns a list of
        ParsedTransaction objects.
        """
        transactions = []

        # Define expected columns and map them to our schema
        column_map = {
            "Date": "transaction_date",
            "Stock": "ticker_symbol",
            "Action": "transaction_type",
            "Qty": "quantity",
            "Price": "price_per_unit",
        }

        # Columns to be summed up for fees
        fee_columns = [
            "STT",
            "Transaction and SEBI Turnover charges",
            "Stamp Duty",
            "Brokerage + Service Tax",
        ]

        required_columns = list(column_map.keys()) + fee_columns

        # Check if all required columns exist
        if not all(col in df.columns for col in required_columns):
            logging.error(
                "ICICI parser: Missing required columns. Expected: %s, Found: %s",
                required_columns,
                df.columns.tolist(),
            )
            # Attempt to proceed if at least the core columns are present
            if not all(col in df.columns for col in column_map.keys()):
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
                df_renamed[col] = 0 # Add column with 0 if it's missing

        df_renamed["fees"] = df_renamed[fee_columns].sum(axis=1)


        # Filter for only buy and sell trades
        df_trades = df_renamed[
            df_renamed["transaction_type"].isin(["Buy", "Sell", "buy", "sell"])
        ].copy()

        # Convert trade_type to uppercase
        df_trades["transaction_type"] = df_trades["transaction_type"].str.upper()

        # Convert date format
        df_trades["transaction_date"] = pd.to_datetime(
            df_trades["transaction_date"], format="%d-%b-%Y"
        ).dt.strftime("%Y-%m-%d")


        for _, row in df_trades.iterrows():
            try:
                # Select only the columns needed for ParsedTransaction
                transaction_data = row[
                    [
                        "ticker_symbol",
                        "transaction_date",
                        "transaction_type",
                        "quantity",
                        "price_per_unit",
                        "fees",
                    ]
                ].to_dict()
                transactions.append(ParsedTransaction(**transaction_data))
            except Exception as e:
                logging.error(
                    f"ICICI parser: Error parsing row: {row.to_dict()}. Error: {e}"
                )

        return transactions
