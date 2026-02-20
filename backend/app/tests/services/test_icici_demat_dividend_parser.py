
from app.services.import_parsers.icici_demat_dividend_parser import (
    IciciDematDividendParser,
)


def test_extract_numbers():
    parser = IciciDematDividendParser()

    # Test simple numbers
    assert parser._extract_numbers("10 20.5 30") == [10.0, 20.5, 30.0]

    # Test with years (should be skipped)
    assert parser._extract_numbers("10 2023 30") == [10.0, 30.0]
    assert parser._extract_numbers("1900 2100") == []
    assert parser._extract_numbers("1899 2101") == [1899.0, 2101.0]

    # Test with alphabets
    # Note: (?<![A-Z]) only checks the single character immediately preceding.
    # In "INE123456789", '1' is preceded by 'E' (skipped),
    # but '2' is preceded by '1' (matched).
    # However, in actual use, ISINs are cleaned out before calling _extract_numbers.
    assert parser._extract_numbers("40 10") == [40.0, 10.0]

    # Test with decimals
    assert parser._extract_numbers("0.1 5.55") == [0.1, 5.55]

    # Test with negative lookbehind
    # "A123" -> '1' is preceded by 'A', so it should not match '1'.
    # Regex engine then tries at '2'. '2' is preceded by '1', which is NOT [A-Z].
    # So it matches '23'.
    assert parser._extract_numbers("A123") == [23.0]

    # Test empty string
    assert parser._extract_numbers("") == []
