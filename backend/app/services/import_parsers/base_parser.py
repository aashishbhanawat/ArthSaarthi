from abc import ABC, abstractmethod

import pandas as pd


from app.schemas.import_session import ParsedTransaction
from typing import List

class BaseParser(ABC):
    """
    Abstract base class for all file parsers.
    """

    @abstractmethod
    def parse(self, df: pd.DataFrame) -> List[ParsedTransaction]:
        """
        Parses the given DataFrame and returns a list of Pydantic models.

        :param df: The pandas DataFrame to be parsed.
        :return: A list of ParsedTransaction objects.
        """
        pass
