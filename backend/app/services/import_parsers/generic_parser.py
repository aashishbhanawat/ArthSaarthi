import logging
from typing import List

import pandas as pd

from app.schemas.import_session import ParsedTransaction

from .base_parser import BaseParser


class GenericCsvParser(BaseParser):
    """
    A generic parser for CSV files that have been pre-processed into a DataFrame.
    """

    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parses a DataFrame and converts it to a list of ParsedTransaction objects.

        :param df: The pandas DataFrame to be parsed. Assumes columns are already
                   named according to the ParsedTransaction schema.
        :return: A list of ParsedTransaction objects.
        """
        transactions = []
        for _, row in df.iterrows():
            try:
                transactions.append(ParsedTransaction(**row.to_dict()))
            except Exception as e:
                logging.error(f"Error parsing row: {row.to_dict()}. Error: {e}")
        return transactions
