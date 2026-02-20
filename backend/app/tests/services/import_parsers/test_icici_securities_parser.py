import pytest
from app.services.import_parsers.icici_securities_parser import ICICISecuritiesParser

@pytest.fixture
def parser():
    return ICICISecuritiesParser()

def test_extract_numbers_simple(parser):
    """Test extracting simple numbers."""
    text = "Transaction No: 12345678, Amount: 1234.56"
    numbers = parser._extract_numbers(text)
    assert numbers == [12345678.0, 1234.56]

def test_extract_numbers_with_commas(parser):
    """Test extracting numbers with commas."""
    text = "Amount: 1,234.56, Price: 1,00,000"
    numbers = parser._extract_numbers(text)
    assert numbers == [1234.56, 100000.0]

def test_extract_numbers_negative(parser):
    """Test extracting negative numbers."""
    text = "Loss: -100.50, Value: -2,000"
    numbers = parser._extract_numbers(text)
    assert numbers == [-100.50, -2000.0]

def test_extract_numbers_mixed(parser):
    """Test extracting numbers from mixed text."""
    text = "100 units at 50.5 each equals 5,050"
    numbers = parser._extract_numbers(text)
    assert numbers == [100.0, 50.5, 5050.0]

def test_extract_numbers_invalid(parser):
    """Test handling of invalid number formats."""
    text = "No numbers here"
    numbers = parser._extract_numbers(text)
    assert numbers == []

def test_extract_numbers_edge_cases(parser):
    """Test edge cases."""
    # Current regex requires digits before dot
    text = "-0.5"
    numbers = parser._extract_numbers(text)
    assert numbers == [-0.5]

    text = "1.0"
    numbers = parser._extract_numbers(text)
    assert numbers == [1.0]

    text = "0.5"
    numbers = parser._extract_numbers(text)
    assert numbers == [0.5]
