import logging
from typing import List

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser


class ZerodhaParser(BaseParser):
    """
    Parser for Zerodha Tradebook CSV files.
    """

    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parses a Zerodha Tradebook DataFrame and returns a list of
        ParsedTransaction objects.
        """
        transactions = []

        # Define expected columns and map them to our schema
        column_map = {
            "symbol": "ticker_symbol",
            "trade_date": "transaction_date",
            "trade_type": "transaction_type",
            "quantity": "quantity",
            "price": "price_per_unit",
            "charges": "fees",
        }

        # Check if all required columns exist
        if not all(col in df.columns for col in column_map.keys()):
            logging.error("Zerodha parser: Missing required columns.")
            return []

        # Rename columns to our internal schema
        df_renamed = df.rename(columns=column_map)

        # Filter for only buy and sell trades
        df_trades = df_renamed[
            df_renamed["transaction_type"].isin(["buy", "sell"])
        ].copy()

        # Convert trade_type to uppercase
        df_trades["transaction_type"] = df_trades["transaction_type"].str.upper()

        for _, row in df_trades.iterrows():
            try:
                transactions.append(ParsedTransaction(**row.to_dict()))
            except Exception as e:
                logging.error(
                    f"Zerodha parser: Error parsing row: {row.to_dict()}. Error: {e}"
                )

        return transactions
