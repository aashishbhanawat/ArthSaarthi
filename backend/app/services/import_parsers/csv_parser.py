import logging

import pandas as pd

from .base_parser import BaseParser


class CsvParser(BaseParser):
    """
    A generic parser for CSV files.
    """

    def parse(self, file_path: str) -> pd.DataFrame:
        """
        Parses a CSV file and returns a DataFrame.

        :param file_path: The path to the CSV file.
        :return: A pandas DataFrame with the transaction data.
        """
        try:
            df = pd.read_csv(file_path)
            # Basic data cleaning and standardization can be done here
            return df
        except Exception as e:
            # It's better to use logging than print for server applications
            logging.error(f"Error parsing CSV file at {file_path}: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
