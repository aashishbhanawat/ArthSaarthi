from .base_parser import BaseParser
from .cams_parser import CamsParser
from .generic_parser import GenericCsvParser
from .icici_parser import IciciParser
from .kfintech_parser import KFintechParser
from .kfintech_xls_parser import KFintechXlsParser
from .mfcentral_parser import MfCentralParser
from .zerodha_coin_parser import ZerodhaCoinParser
from .zerodha_parser import ZerodhaParser


def get_parser(source_type: str) -> BaseParser:
    if source_type == "Zerodha Tradebook":
        return ZerodhaParser()
    elif source_type == "ICICI Direct Tradebook":
        return IciciParser()
    elif source_type == "MFCentral CAS":
        return MfCentralParser()
    elif source_type == "CAMS Statement":
        return CamsParser()
    elif source_type == "Zerodha Coin":
        return ZerodhaCoinParser()
    elif source_type == "KFintech Statement":
        return KFintechParser()
    elif source_type == "KFintech XLS":
        return KFintechXlsParser()
    # Add other parsers here in the future
    else:
        return GenericCsvParser()



