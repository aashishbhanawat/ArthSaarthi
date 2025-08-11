from .base_parser import BaseParser
from .generic_parser import GenericCsvParser
from .icici_parser import IciciParser
from .zerodha_parser import ZerodhaParser


def get_parser(source_type: str) -> BaseParser:
    if source_type == "Zerodha Tradebook":
        return ZerodhaParser()
    elif source_type == "ICICI Direct Tradebook":
        return IciciParser()
    # Add other parsers here in the future
    else:
        return GenericCsvParser()
