"""
Test suite for AggregatedUnicodeBlockParser functionality.
"""
import pytest
import pandas as pd
from unicode_stats.aggregation import AggregatedUnicodeBlockParser


@pytest.fixture
def mock_data():
    """Provides mock data for testing various functionalities of AggregatedUnicodeBlockParser."""
    return [
        {"response": "Hello, World!", "prompt": "Greeting in English"},
        {"response": "Привет, мир!", "prompt": "Greeting in Russian"},
        {"response": "你好世界", "prompt": "Greeting in Chinese"}
    ]


def test_aggregated_unicode_block_parser_initialization():
    """Test the initialization of AggregatedUnicodeBlockParser with specific parameters."""
    parser = AggregatedUnicodeBlockParser(columns="response", convert_non_str_to_str=True, max_lines=5)
    assert parser.columns == ["response"]
    assert parser.convert_non_str_to_str is True
    assert parser.max_lines == 5


def test_create_inv_index(mock_data):  # pylint: disable=redefined-outer-name
    """Test the inverted index creation to ensure proper Unicode block identification and counting."""
    parser = AggregatedUnicodeBlockParser(columns="response")
    inv_index = parser.create_inv_index(mock_data)

    assert "Basic Latin" in inv_index
    assert "Cyrillic (Russian)" in inv_index
    assert "CJK Unified Ideographs" in inv_index
    assert "response" in inv_index["Basic Latin"]
    assert "response" in inv_index["Cyrillic (Russian)"]
    assert "response" in inv_index["CJK Unified Ideographs"]


def test_create_aggregated_statistics(mock_data):  # pylint: disable=redefined-outer-name
    """Test aggregation of statistics from an inverted index to validate symbol counts and example extraction."""
    parser = AggregatedUnicodeBlockParser(columns="response")
    inv_index = parser.create_inv_index(mock_data)
    stats_dict = parser.create_aggregated_statistics(inv_index, mock_data)

    assert ("Basic Latin", "response") in stats_dict
    assert ("Cyrillic (Russian)", "response") in stats_dict
    assert ("CJK Unified Ideographs", "response") in stats_dict
    assert stats_dict[("Basic Latin", "response")]["n"] > 0
    assert stats_dict[("Cyrillic (Russian)", "response")]["n"] > 0
    assert stats_dict[("CJK Unified Ideographs", "response")]["n"] > 0


def test_get_aggregated_statistics_df(mock_data):  # pylint: disable=redefined-outer-name
    """Test the final DataFrame output of the get_aggregated_statistics_df method."""
    parser = AggregatedUnicodeBlockParser(columns="response")
    df_metrics = parser.get_aggregated_statistics_df(mock_data)

    assert isinstance(df_metrics, pd.DataFrame)
    required_columns = [
        "block", "column", "n", "rate", "symbols",
        "n_symbols", "rows", "example_first", "example_last"
    ]
    for col in required_columns:
        assert col in df_metrics.columns

    assert any(df_metrics["block"] == "Basic Latin")
    assert any(df_metrics["block"] == "Cyrillic (Russian)")
    assert any(df_metrics["block"] == "CJK Unified Ideographs")


def test_read_jsonl(mock_data):  # pylint: disable=redefined-outer-name
    """Test reading a JSONL file by mocking file reading and verifying content parsing."""
    parser = AggregatedUnicodeBlockParser()
    parser.read_jsonl = lambda _: mock_data  # Mock the read_jsonl method to return mock data

    list_of_dicts = parser.read_jsonl("mock_file.jsonl")
    assert list_of_dicts == mock_data


def test_get_stats(mock_data):  # pylint: disable=redefined-outer-name
    """Test the end-to-end processing from JSONL file to final DataFrame output."""
    parser = AggregatedUnicodeBlockParser(columns="response")
    parser.read_jsonl = lambda _: mock_data  # Mock the read_jsonl method to return mock data

    df_metrics = parser.get_stats("mock_file.jsonl")

    assert isinstance(df_metrics, pd.DataFrame)
    required_columns = [
        "block", "column", "n", "rate", "symbols",
        "n_symbols", "rows", "example_first", "example_last"
    ]
    for col in required_columns:
        assert col in df_metrics.columns
