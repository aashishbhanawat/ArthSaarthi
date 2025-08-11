from .base_parser import BaseParser
from .generic_parser import GenericCsvParser
from .zerodha_parser import ZerodhaParser


def get_parser(source_type: str) -> BaseParser:
    if source_type == "Zerodha Tradebook":
        return ZerodhaParser()
    # Add other parsers here in the future
    else:
        return GenericCsvParser()
