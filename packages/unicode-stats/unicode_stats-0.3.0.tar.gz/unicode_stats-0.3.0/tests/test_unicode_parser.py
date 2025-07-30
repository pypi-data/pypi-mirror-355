"""
Test cases for the UnicodeBlockParser class.
"""


import pytest
from unicode_stats.unicode_parser import UnicodeBlockParser


@pytest.fixture
def parser():
    return UnicodeBlockParser()


def test_single_block(parser):  # pylint: disable=redefined-outer-name
    """Test the get_single_block method for various characters."""
    assert parser.get_single_block("A") == "Basic Latin"
    assert parser.get_single_block("П") == "Cyrillic (Russian)"
    assert parser.get_single_block("Σ") == "Greek and Coptic"


def test_stats(parser):  # pylint: disable=redefined-outer-name
    """Test the get_stats method for a string containing multiple Unicode blocks."""
    text = "Hello, Привет!"
    stats = parser.get_stats(text)
    assert "Basic Latin" in stats
    assert "Cyrillic (Russian)" in stats
    assert stats["Basic Latin"]["n"] > 0
    assert stats["Cyrillic (Russian)"]["n"] > 0


def test_language_detection(parser):  # pylint: disable=redefined-outer-name
    """Test the get_single_lang and get_all_lang methods for language detection."""
    assert parser.get_lang("Hello, World!") == "en"
    assert parser.get_lang("Привет, мир!") == "ru"
    assert parser.get_lang("こんにちは") == "Hiragana"
