import pandas as pd

from .base_parser import BaseParser


class ZerodhaParser(BaseParser):
    """
    Parser for Zerodha statements (CSV/PDF).
    """

    def parse(self, df: pd.DataFrame) -> list:
        """
        Parses a Zerodha statement and returns a list of Pydantic models.

        :param df: The pandas DataFrame to be parsed.
        :return: A list of ParsedTransaction objects.
        """
        # TODO: Implement Zerodha-specific parsing logic
        raise NotImplementedError("Zerodha parser is not yet implemented.")
