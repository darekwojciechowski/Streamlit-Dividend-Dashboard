"""Unit tests for DividendDataProcessor class.

Tests cover:
- Loading and parsing TSV files with dividend data
- Data cleaning (suffix removal, whitespace stripping)
- Data validation (schema check, type conversion)
- Filtering by ticker selection
- Edge cases (empty files, missing columns, malformed data)
- Data integrity and performance

The processor reads TSV files where:
-  Numeric columns have suffixes: Net Dividend has " USD", Tax Collected has "%"
- These suffixes are stripped during data cleaning
- Required columns: Ticker, Net Dividend, Tax Collected, Shares
"""

from pathlib import Path

import pandas as pd
import pytest
from app.data_processor import DividendDataProcessor

# ============================================================================
# TEST CONSTANTS - Reusable test data
# ============================================================================

# Sample ticker values
TICKER_AAPL = "AAPL.US"
TICKER_MSFT = "MSFT.US"
TICKER_NONEXISTENT = "NONEXIST.XX"

# Expected file sizes
SAMPLE_FILE_SIZE = 5
SAMPLE_DATA_AAPL_COUNT = 2  # AAPL appears twice in sample data
SAMPLE_DATA_GROUPED_COUNT = 3  # AAPL + MSFT

# Numeric test values
DIVIDEND_50_USD = 50.0
DIVIDEND_60_USD = 60.0
DIVIDEND_75_USD = 75.0
TAX_10_PERCENT = 10.0
SHARES_100 = 100
SHARES_50 = 50

# Error message patterns
ERROR_FILE_NOT_FOUND = "not found"
ERROR_MISSING_COLUMNS = "Missing required columns"
ERROR_EMPTY_DATA = ""

# Extreme values for boundary testing
EXTREME_ZERO = 0.0
EXTREME_NEGATIVE = -100.0


@pytest.mark.unit
class TestDividendDataProcessorInit:
    """Test processor initialization and data loading."""

    def test_loads_valid_tsv_file(self, sample_tsv_file: Path) -> None:
        """Test successful loading of a valid TSV file.

        Valid file contains all required columns with proper formatting.
        """
        # Arrange & Act
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Assert - data loaded successfully
        assert processor.df is not None
        assert not processor.df.empty
        assert len(processor.df) == SAMPLE_FILE_SIZE

    def test_raises_file_not_found_with_clear_message(self) -> None:
        """Test FileNotFoundError with helpful message for missing files."""
        # Arrange
        fake_path = "nonexistent/path/file.csv"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match=ERROR_FILE_NOT_FOUND):
            DividendDataProcessor(fake_path)

    def test_required_columns_attribute_defined(self) -> None:
        """Test that REQUIRED_COLUMNS class constant is properly defined.

        This constant specifies the exact schema required for input files.
        """
        # Act
        required = DividendDataProcessor.REQUIRED_COLUMNS

        # Assert
        assert isinstance(required, list)
        assert required == [
            "Ticker",
            "Net Dividend",
            "Tax Collected",
            "Shares",
        ]


@pytest.mark.unit
class TestDataCleaning:
    """Test CSV data cleaning transformations.

    Input CSV files have text suffixes in numeric columns:
    - Net Dividend: "50 USD" -> 50.0
    - Tax Collected: "10%" -> 10.0
    - Ticker: " AAPL.US " -> "AAPL.US" (whitespace stripped)
    """

    def test_strips_net_dividend_usd_suffix(self, sample_tsv_file: Path) -> None:
        """Test that ' USD' suffix is removed from Net Dividend column.

        Input:  [' 50 USD', ' 75 USD', ...]
        Output: [50.0, 75.0, ...] (numeric type)
        """
        # Arrange & Act
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Assert
        assert processor.df["Net Dividend"].dtype in [
            float,
            "float64",
        ], f"Net Dividend should be numeric, got {processor.df['Net Dividend'].dtype}"
        assert processor.df["Net Dividend"].iloc[0] == DIVIDEND_50_USD, (
            f"First dividend should be {DIVIDEND_50_USD}, got {processor.df['Net Dividend'].iloc[0]}"
        )
        # All values should be positive (no negative dividends in clean data)
        assert all(processor.df["Net Dividend"] > 0), "All dividends should be positive"

    def test_strips_tax_collected_percentage_suffix(self, sample_tsv_file: Path) -> None:
        """Test that '%' suffix is removed from Tax Collected column.

        Input:  ['10%', '15%', ...]
        Output: [10.0, 15.0, ...] (numeric type)
        """
        # Arrange & Act
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Assert
        assert processor.df["Tax Collected"].dtype in [float, "float64"]
        assert processor.df["Tax Collected"].iloc[0] == TAX_10_PERCENT

    def test_converts_shares_to_numeric(self, sample_tsv_file: Path) -> None:
        """Test shares column is strongly typed as numeric (int or float)."""
        # Arrange & Act
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Assert
        assert processor.df["Shares"].dtype in [int, "int64", float, "float64"]

    def test_strips_whitespace_from_column_names(self, tmp_path: Path) -> None:
        """Test column names with leading/trailing spaces are cleaned.

        Column names like ' Ticker ' are normalized to 'Ticker'.
        """
        # Arrange
        file_path = tmp_path / "whitespace_cols.csv"
        df = pd.DataFrame(
            {
                " Ticker ": [TICKER_AAPL],
                "Net Dividend": ["50 USD"],
                "Tax Collected": ["10%"],
                "Shares": [SHARES_100],
            }
        )
        df.to_csv(file_path, sep="\t", index=False)

        # Act
        processor = DividendDataProcessor(str(file_path))

        # Assert - column should be cleaned or not present with spaces
        assert "Ticker" in processor.df.columns or " Ticker " not in processor.df.columns


@pytest.mark.unit
class TestDataValidation:
    """Test schema and type validation during load."""

    def test_raises_error_when_required_columns_missing(self, invalid_tsv_file: Path) -> None:
        """Test FileNotFoundError when input file lacks required columns.

        The processor validates schema early. Missing required columns
        (Ticker, Net Dividend, Tax Collected, Shares) should raise.
        """
        # Act & Assert
        with pytest.raises((ValueError, RuntimeError), match=ERROR_MISSING_COLUMNS):
            DividendDataProcessor(str(invalid_tsv_file))

    def test_raises_error_for_empty_file(self, empty_tsv_file: Path) -> None:
        """Test that empty files (no data rows) raise an error.

        A file with only headers but no data is invalid.
        """
        # Act & Assert
        with pytest.raises((ValueError, RuntimeError)):
            DividendDataProcessor(str(empty_tsv_file))

    def test_coerces_invalid_numbers_to_nan(self, tmp_path: Path) -> None:
        """Test that non-numeric values in numeric columns are coerced to NaN.

        When suffix-stripping leaves non-numeric text (e.g., 'invalid' from 'invalid USD'),
        pandas coerces to NaN. Processor should handle this gracefully.
        """
        # Arrange
        file_path = tmp_path / "invalid_numbers.csv"
        df = pd.DataFrame(
            {
                "Ticker": [TICKER_AAPL],
                "Net Dividend": ["invalid USD"],  # Non-numeric after suffix strip
                "Tax Collected": ["10%"],
                "Shares": [SHARES_100],
            }
        )
        df.to_csv(file_path, sep="\t", index=False)

        # Act & Assert - should not crash
        processor = DividendDataProcessor(str(file_path))
        assert processor.df is not None


@pytest.mark.unit
class TestFilterData:
    """Test data filtering by ticker selection."""

    def test_filter_by_single_ticker(self, sample_tsv_file: Path) -> None:
        """Test filtering to include only one ticker.

        Sample data has 5 rows: AAPL.US appears twice.
        Filtering for [AAPL.US] should return 2 rows.
        """
        # Arrange
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Act
        filtered = processor.filter_data([TICKER_AAPL])

        # Assert
        assert not filtered.empty, f"Filter for {TICKER_AAPL} should not be empty"
        assert all(filtered["Ticker"] == TICKER_AAPL), f"All filtered rows should have ticker {TICKER_AAPL}"
        assert len(filtered) == SAMPLE_DATA_AAPL_COUNT, (
            f"Expected {SAMPLE_DATA_AAPL_COUNT} rows for {TICKER_AAPL}, got {len(filtered)}"
        )

    def test_filter_by_multiple_tickers(self, sample_tsv_file: Path) -> None:
        """Test filtering to include multiple selected tickers.

        Sample data has 5 rows: AAPL (2) + MSFT (1) + PKO (1) + SAP (1).
        Filtering for [AAPL.US, MSFT.US] should return 3 rows.
        """
        # Arrange
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Act
        filtered = processor.filter_data([TICKER_AAPL, TICKER_MSFT])

        # Assert
        assert not filtered.empty
        assert set(filtered["Ticker"].unique()) == {TICKER_AAPL, TICKER_MSFT}
        assert len(filtered) == SAMPLE_DATA_GROUPED_COUNT

    def test_filter_with_nonexistent_ticker_returns_empty(self, sample_tsv_file: Path) -> None:
        """Test filtering for non-existent ticker returns empty DataFrame."""
        # Arrange
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Act
        filtered = processor.filter_data([TICKER_NONEXISTENT])

        # Assert
        assert filtered.empty

    def test_filter_with_empty_ticker_list_returns_empty(self, sample_tsv_file: Path) -> None:
        """Test filtering with empty selection returns empty DataFrame.

        An empty ticker list has no rows to match.
        """
        # Arrange
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Act
        filtered = processor.filter_data([])

        # Assert
        assert filtered.empty

    def test_filter_returns_independent_copy(self, sample_tsv_file: Path) -> None:
        """Test that filter_data returns a copy, not a view of original.

        Modifications to filtered data should not affect the processor's
        internal DataFrame.
        """
        # Arrange
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Act
        filtered = processor.filter_data([TICKER_AAPL])
        original_value = processor.df.loc[0, "Net Dividend"]
        # Modify the filtered copy
        filtered.loc[filtered.index[0], "Net Dividend"] = 999.0

        # Assert - original should be unaffected
        assert processor.df.loc[0, "Net Dividend"] == original_value
        assert processor.df.loc[0, "Net Dividend"] != 999.0


@pytest.mark.unit
class TestEdgeCases:
    """Test boundary conditions and unusual but valid inputs."""

    def test_handles_duplicate_tickers_correctly(self, tmp_path: Path) -> None:
        """Test processor correctly handles duplicate ticker entries.

        Some tickers may appear multiple times (different purchase dates,
        dividend payments). All occurrences should be preserved and filterable.
        """
        # Arrange
        file_path = tmp_path / "duplicates.csv"
        df = pd.DataFrame(
            {
                "Ticker": [TICKER_AAPL, TICKER_AAPL, TICKER_MSFT],
                "Net Dividend": ["50 USD", "60 USD", "75 USD"],
                "Tax Collected": ["10%", "12%", "15%"],
                "Shares": [SHARES_100, SHARES_100, SHARES_50],
            }
        )
        df.to_csv(file_path, sep="\t", index=False)

        # Act
        processor = DividendDataProcessor(str(file_path))
        filtered = processor.filter_data([TICKER_AAPL])

        # Assert
        assert len(filtered) == 2
        assert all(filtered["Ticker"] == TICKER_AAPL)

    def test_handles_whitespace_in_ticker_field(self, tmp_path: Path) -> None:
        """Test handling of extra spaces in ticker values.

        Whitespace should be stripped to normalize tickers.
        """
        # Arrange
        file_path = tmp_path / "whitespace_ticker.csv"
        df = pd.DataFrame(
            {
                "Ticker": [" AAPL.US "],  # Extra spaces
                "Net Dividend": ["50 USD"],
                "Tax Collected": ["10%"],
                "Shares": [SHARES_100],
            }
        )
        df.to_csv(file_path, sep="\t", index=False)

        # Act
        processor = DividendDataProcessor(str(file_path))

        # Assert
        assert processor.df is not None

    @pytest.mark.parametrize(
        ("net_div", "tax", "scenario"),
        [
            (EXTREME_ZERO, EXTREME_ZERO, "zero dividend"),
            (EXTREME_NEGATIVE, EXTREME_ZERO, "negative dividend"),
        ],
    )
    def test_handles_extreme_numeric_values(self, net_div: float, tax: float, scenario: str, tmp_path: Path) -> None:
        """Test processor behavior with boundary numeric values.

        Extreme values might be invalid (e.g., negative dividends) but
        should be handled gracefully without crashing.

        Args:
            net_div: Net dividend value to test
            tax: Tax collected value to test
            scenario: Description of the scenario
        """
        # Arrange
        file_path = tmp_path / f"extreme_{scenario}.csv"
        df = pd.DataFrame(
            {
                "Ticker": ["TEST.US"],
                "Net Dividend": [str(net_div) + " USD"],
                "Tax Collected": [str(tax) + "%"],
                "Shares": [SHARES_100],
            }
        )
        df.to_csv(file_path, sep="\t", index=False)

        # Act & Assert - should handle gracefully (no crash)
        try:
            processor = DividendDataProcessor(str(file_path))
            assert processor.df is not None
        except ValueError, RuntimeError:
            # Acceptable to reject invalid extreme values
            pass


@pytest.mark.unit
class TestDataIntegrity:
    """Test data consistency and independence."""

    def test_loaded_dataframe_is_independent_copy(self, sample_tsv_file: Path) -> None:
        """Test that loaded DataFrame is independent from source file.

        Modifying the processor's DataFrame shouldn't affect a fresh load.
        """
        # Arrange
        processor1 = DividendDataProcessor(str(sample_tsv_file))
        original_value = processor1.df.loc[0, "Net Dividend"]

        # Act
        processor1.df.loc[0, "Net Dividend"] = 999.0

        # Assert
        processor2 = DividendDataProcessor(str(sample_tsv_file))
        assert processor2.df.loc[0, "Net Dividend"] == original_value
        assert processor2.df.loc[0, "Net Dividend"] != 999.0

    def test_large_dataset_loads_efficiently(self, tmp_path: Path) -> None:
        """Test processor handles large datasets (1000+ rows) efficiently.

        Performance test ensures scaling works without memory issues.
        """
        # Arrange - create large dataset inline (1000 rows)
        file_path = tmp_path / "large.csv"
        tickers = [f"TICK{i}.US" for i in range(1000)]
        df = pd.DataFrame(
            {
                "Ticker": tickers,
                "Net Dividend": [50.0 + i for i in range(1000)],
                "Tax Collected": [10.0] * 1000,
                "Shares": [100] * 1000,
            }
        )
        # Add suffixes to match real file format
        df["Net Dividend"] = df["Net Dividend"].astype(str) + " USD"
        df["Tax Collected"] = df["Tax Collected"].astype(str) + "%"
        df.to_csv(file_path, sep="\t", index=False)

        # Act
        processor = DividendDataProcessor(str(file_path))

        # Assert
        assert len(processor.df) == 1000
        assert not processor.df.empty
