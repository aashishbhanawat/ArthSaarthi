from .base_parser import BaseParser


def get_parser(source_type: str) -> BaseParser:
    """Return the appropriate parser for the given source type.

    Parsers are lazily imported to avoid loading heavy libraries
    (pdfplumber, pdfminer, pandas, openpyxl) at application startup.
    """
    if source_type == "Zerodha Tradebook":
        from .zerodha_parser import ZerodhaParser
        return ZerodhaParser()
    elif source_type == "ICICI Direct Tradebook":
        from .icici_parser import IciciParser
        return IciciParser()
    elif source_type == "ICICI Direct Portfolio Equity":
        from .icici_portfolio_parser import IciciPortfolioParser
        return IciciPortfolioParser()
    elif source_type == "MFCentral CAS":
        from .mfcentral_parser import MfCentralParser
        return MfCentralParser()
    elif source_type == "CAMS Statement":
        from .cams_parser import CamsParser
        return CamsParser()
    elif source_type == "Zerodha Coin":
        from .zerodha_coin_parser import ZerodhaCoinParser
        return ZerodhaCoinParser()
    elif source_type == "KFintech Statement":
        from .kfintech_parser import KFintechParser
        return KFintechParser()
    elif source_type == "KFintech XLS":
        from .kfintech_xls_parser import KFintechXlsParser
        return KFintechXlsParser()
    elif source_type == "ICICI Securities MF":
        from .icici_securities_parser import ICICISecuritiesParser
        return ICICISecuritiesParser()
    elif source_type == "Zerodha Dividend":
        from .zerodha_dividend_parser import ZerodhaDividendParser
        return ZerodhaDividendParser()
    elif source_type == "ICICI DEMAT Dividend":
        from .icici_demat_dividend_parser import IciciDematDividendParser
        return IciciDematDividendParser()
    elif source_type == "HDFC Bank FD Statement":
        from .hdfc_fd_parser import HdfcFdParser
        return HdfcFdParser()
    elif source_type == "ICICI Bank FD Statement":
        from .icici_fd_parser import IciciFdParser
        return IciciFdParser()
    elif source_type == "SBI FD Statement":
        from .sbi_fd_parser import SbiFdParser
        return SbiFdParser()
    # Add other parsers here in the future
    else:
        from .generic_parser import GenericCsvParser
        return GenericCsvParser()
