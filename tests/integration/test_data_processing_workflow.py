"""Integration tests for data processing workflow.

Tests verify the complete data flow:
1. Load TSV file with dividend data
2. Clean (strip suffixes, whitespace)
3. Validate schema (required columns)
4. Filter by ticker selection

These tests use real file I/O and actual data processor implementation.
"""

import pytest
from pathlib import Path

from app.data_processor import DividendDataProcessor


@pytest.mark.integration
class TestDataProcessingWorkflow:
    """Test data processor component and workflows."""

    def test_complete_workflow_load_clean_filter(self, sample_tsv_file: Path) -> None:
        """Test complete data processing workflow.

        Workflow:
        1. Load TSV file from path
        2. Data is automatically cleaned (suffixes removed)
        3. Validate required columns exist
        4. Filter by selected tickers
        """
        # Setup
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Verify data loaded and cleaned
        assert processor.df is not None
        assert not processor.df.empty
        assert len(processor.df) == 5  # Sample has 5 rows

        # Verify columns exist
        assert "Ticker" in processor.df.columns
        assert "Net Dividend" in processor.df.columns
        assert "Tax Collected" in processor.df.columns
        assert "Shares" in processor.df.columns

        # Verify data is numeric (no ' USD' or '%' suffixes)
        assert processor.df["Net Dividend"].dtype in [
            "float64",
            "int64",
        ], "Net Dividend should be numeric after cleaning"

        assert processor.df["Tax Collected"].dtype in [
            "float64",
            "int64",
        ], "Tax Collected should be numeric after cleaning"

    def test_filter_by_single_ticker(self, sample_tsv_file: Path) -> None:
        """Test filtering data for a single ticker.

        Given:
        - Processor with 5 rows and multiple tickers
        When:
        - Filter for single ticker (AAPL.US appears twice)
        Then:
        - Result should contain only that ticker's rows
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Filter for AAPL only (appears 2 times in sample data)
        filtered = processor.filter_data(["AAPL.US"])

        assert filtered is not None
        assert not filtered.empty
        assert len(filtered) == 2
        assert (filtered["Ticker"] == "AAPL.US").all()

    def test_filter_by_multiple_tickers(self, sample_tsv_file: Path) -> None:
        """Test filtering data for multiple tickers.

        Given:
        - Processor with 5 rows across 4 tickers
        When:
        - Filter for 2 specific tickers
        Then:
        - Result should contain only rows with those tickers
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Filter for specific tickers
        selected = ["AAPL.US", "MSFT.US"]
        filtered = processor.filter_data(selected)

        assert filtered is not None
        assert not filtered.empty
        assert set(filtered["Ticker"].unique()) == set(selected)

    def test_filter_returns_empty_for_nonexistent_ticker(
        self, sample_tsv_file: Path
    ) -> None:
        """Test filtering for ticker not in data returns empty DataFrame.

        Given:
        - Processor with sample data
        When:
        - Filter for ticker that doesn't exist
        Then:
        - Return empty DataFrame (not error)
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        filtered = processor.filter_data(["NONEXISTENT.XX"])

        assert filtered is not None
        assert filtered.empty

    def test_filter_with_empty_selection_returns_empty(
        self, sample_tsv_file: Path
    ) -> None:
        """Test filtering with empty ticker list returns empty DataFrame.

        Given:
        - Processor with sample data
        When:
        - Filter with empty ticker list
        Then:
        - Return empty DataFrame
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        filtered = processor.filter_data([])

        assert filtered is not None
        assert filtered.empty

    def test_data_remains_unchanged_after_filtering(
        self, sample_tsv_file: Path
    ) -> None:
        """Test that filtering doesn't modify original processor data.

        Given:
        - Processor with sample data
        When:
        - Filter data multiple times
        Then:
        - Original processor.df remains unchanged
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        original_size = len(processor.df)

        # Filter multiple times
        processor.filter_data(["AAPL.US"])
        processor.filter_data(["MSFT.US"])
        processor.filter_data([])

        # Original should be unchanged
        assert len(processor.df) == original_size

    def test_filtered_data_contains_all_required_columns(
        self, sample_tsv_file: Path
    ) -> None:
        """Test that filtered data preserves all required columns.

        Given:
        - Processor with sample data
        When:
        - Filter for specific tickers
        Then:
        - Result contains all required columns with correct types
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        filtered = processor.filter_data(["AAPL.US", "MSFT.US"])

        required_cols = ["Ticker", "Net Dividend", "Tax Collected", "Shares"]
        assert all(col in filtered.columns for col in required_cols)

        # Verify numeric columns are actually numeric
        assert filtered["Net Dividend"].dtype in ["float64", "int64"]
        assert filtered["Tax Collected"].dtype in ["float64", "int64"]
        assert filtered["Shares"].dtype in ["float64", "int64"]


@pytest.mark.integration
class TestDataCleaningIntegration:
    """Test data cleaning as part of full workflow."""

    def test_net_dividend_suffix_removed(self, sample_tsv_file: Path) -> None:
        """Test that ' USD' suffix is removed from Net Dividend.

        Given:
        - TSV file with ' USD' suffix in Net Dividend
        When:
        - Load file via processor
        Then:
        - Values are numeric without suffix
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Values should be numeric floats, not strings with ' USD'
        assert all(
            isinstance(val, (int, float)) for val in processor.df["Net Dividend"]
        )

        # Check no ' USD' in values (would fail if not cleaned)
        df_as_str = processor.df.astype(str)
        assert not df_as_str["Net Dividend"].str.contains(" USD").any()

    def test_tax_collected_percent_suffix_removed(self, sample_tsv_file: Path) -> None:
        """Test that '%' suffix is removed from Tax Collected.

        Given:
        - TSV file with '%' suffix in Tax Collected
        When:
        - Load file via processor
        Then:
        - Values are numeric without suffix
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Values should be numeric floats, not strings with '%'
        assert all(
            isinstance(val, (int, float)) for val in processor.df["Tax Collected"]
        )

        # Check no '%' in values (would fail if not cleaned)
        df_as_str = processor.df.astype(str)
        assert not df_as_str["Tax Collected"].str.contains("%").any()

    def test_whitespace_stripped_from_columns(self, sample_tsv_file: Path) -> None:
        """Test that column names have whitespace stripped.

        Given:
        - TSV file that might have whitespace in column names
        When:
        - Load file via processor
        Then:
        - Column names are clean (no leading/trailing spaces)
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        # No column should have leading/trailing spaces
        assert all(col == col.strip() for col in processor.df.columns)
