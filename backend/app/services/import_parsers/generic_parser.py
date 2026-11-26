import logging
from typing import List

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser


class GenericCsvParser(BaseParser):
    """
    A generic parser for CSV files that have been pre-processed into a DataFrame.
    """

    REQUIRED_COLUMNS = {
        "ticker_symbol",
        "transaction_type",
        "quantity",
        "price_per_unit",
        "transaction_date",
    }

    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parses a DataFrame and converts it to a list of ParsedTransaction objects.

        :param df: The pandas DataFrame to be parsed. Assumes columns are already
                   named according to the ParsedTransaction schema.
        :return: A list of ParsedTransaction objects.
        """
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        missing = sorted(self.REQUIRED_COLUMNS - set(df.columns))
        if missing:
            raise ValueError(
                f"Missing required CSV headers: {', '.join(missing)}. "
                f"Required headers: {', '.join(sorted(self.REQUIRED_COLUMNS))}."
            )

        transactions = []
        row_errors = []
        for idx, row in df.iterrows():
            try:
                transactions.append(ParsedTransaction(**row.to_dict()))
            except Exception as e:
                logging.error(f"Error parsing row: {row.to_dict()}. Error: {e}")
                if len(row_errors) < 3:
                    row_errors.append(f"Row {int(idx) + 2}: {e}")

        if not transactions and row_errors:
            raise ValueError(
                f"No valid transactions found. Sample errors: {'; '.join(row_errors)}"
            )
        return transactions
