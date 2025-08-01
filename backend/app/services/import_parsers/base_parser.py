from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd

class BaseParser(ABC):
    """
    Abstract base class for all file parsers.
    """

    @abstractmethod
    def parse(self, file_path: str) -> pd.DataFrame:
        """
        Parses the given file and returns a pandas DataFrame with standardized column names.

        :param file_path: The path to the file to be parsed.
        :return: A pandas DataFrame containing the extracted transaction data.
        """
        pass
