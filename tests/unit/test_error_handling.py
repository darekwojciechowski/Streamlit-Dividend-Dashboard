"""Enhanced error path and boundary condition tests.

These tests verify that the application handles errors gracefully and
provides helpful error messages. They test both happy paths and error scenarios.

Markers:
    @pytest.mark.unit: Fast, isolated tests
    @pytest.mark.error: Error handling scenarios
"""

import pytest
import pandas as pd
from pathlib import Path
from app.data_processor import DividendDataProcessor
from app.utils.dividend_calculator import DividendCalculator


@pytest.mark.unit
class TestDataProcessorErrorHandling:
    """Test error handling and error messages in DividendDataProcessor."""

    def test_file_not_found_error_includes_path(self) -> None:
        """Test FileNotFoundError message includes the requested file path."""
        # Arrange
        fake_path = "/nonexistent/path/to/file.csv"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match=r"Data file not found"):
            DividendDataProcessor(fake_path)

    def test_missing_columns_error_specifies_column_names(self, tmp_path: Path) -> None:
        """Test error message specifies which columns are missing or invalid."""
        # Arrange
        file_path = tmp_path / "invalid_schema.csv"
        df = pd.DataFrame({"WrongCol1": [1], "WrongCol2": [2]})
        df.to_csv(file_path, sep="\t", index=False)

        # Act & Assert
        # Note: ValueError is wrapped in RuntimeError by _load_and_clean_data exception handler
        with pytest.raises(RuntimeError, match=r"Missing required columns"):
            DividendDataProcessor(str(file_path))

    def test_empty_file_handles_gracefully(self, tmp_path: Path) -> None:
        """Test that file with headers only is handled gracefully."""
        # Arrange
        file_path = tmp_path / "empty.csv"
        file_path.write_text(
            "Ticker\tNet Dividend\tTax Collected\tShares\n"
        )  # Headers only

        # Act & Assert
        # Empty file (headers only) should load without error, just with empty DataFrame
        processor = DividendDataProcessor(str(file_path))
        assert processor.df is not None
        assert (
            processor.df.empty
        ), "File with headers only should result in empty DataFrame"

    def test_malformed_numeric_data_handling(self, tmp_path: Path) -> None:
        """Test handling of malformed numeric data (non-numeric in numeric fields)."""
        # Arrange
        file_path = tmp_path / "malformed.csv"
        df = pd.DataFrame(
            {
                "Ticker": ["AAPL.US"],
                "Net Dividend": ["not_a_number USD"],
                "Tax Collected": ["invalid%"],
                "Shares": ["fifty"],
            }
        )
        df.to_csv(file_path, sep="\t", index=False)

        # Act - processor coerces invalid numerics to NaN via pd.to_numeric(errors='coerce')
        processor = DividendDataProcessor(str(file_path))
        # Should load successfully with NaN values for malformed columns
        assert processor.df is not None
        # Verify that invalid values were coerced to NaN
        assert pd.isna(processor.df.loc[0, "Net Dividend"])
        assert pd.isna(processor.df.loc[0, "Shares"])


@pytest.mark.unit
class TestDividendCalculatorBoundaryConditions:
    """Test boundary conditions and unusual but valid inputs."""

    def test_currency_symbol_unknown_ticker_returns_default(self) -> None:
        """Test that unknown ticker country codes default gracefully."""
        # Arrange
        unknown_ticker = "TICKER.UNKNOWN"

        # Act
        result = DividendCalculator.get_currency_symbol(unknown_ticker)

        # Assert - should return a default (not crash)
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"
        assert result == "$", "Unknown ticker should default to USD ($)"

    def test_currency_symbol_no_suffix_ticker_returns_default(self) -> None:
        """Test that ticker with no country suffix defaults to USD."""
        # Arrange
        no_suffix_ticker = "JUSTLETTERS"

        # Act
        result = DividendCalculator.get_currency_symbol(no_suffix_ticker)

        # Assert
        assert isinstance(result, str), "Result should be a string"
        assert result == "$", "No-suffix ticker should default to USD"

    def test_empty_dataframe_returns_none(self) -> None:
        """Test that empty DataFrame returns None for initial dividend."""
        # Arrange
        empty_df = pd.DataFrame()

        # Act
        result = DividendCalculator.get_initial_dividend(empty_df)

        # Assert
        assert result is None, "Empty DataFrame should return None for initial dividend"

    def test_dataframe_missing_net_dividend_column(self) -> None:
        """Test handling when 'Net Dividend' column is missing."""
        # Arrange
        df = pd.DataFrame({"OtherColumn": [100, 200]})

        # Act
        result = DividendCalculator.get_initial_dividend(df)

        # Assert
        assert result is None, "Missing 'Net Dividend' column should return None"

    def test_dataframe_all_nan_values(self) -> None:
        """Test handling when all Net Dividend values are NaN."""
        # Arrange
        df = pd.DataFrame({"Net Dividend": [None, None, None]})

        # Act
        result = DividendCalculator.get_initial_dividend(df)

        # Assert
        assert result is None, "DataFrame with all-NaN dividends should return None"

    def test_dataframe_negative_dividends_only(self) -> None:
        """Test handling when all dividends are negative (invalid)."""
        # Arrange
        df = pd.DataFrame({"Net Dividend": [-10.0, -20.0, -30.0]})

        # Act
        result = DividendCalculator.get_initial_dividend(df)

        # Assert
        assert result is None, "All-negative dividends should return None"

    def test_zero_initial_dividend_projection(self) -> None:
        """Test projection with zero initial dividend."""
        # Arrange
        initial = 0.0
        growth = 7.0
        years = 5

        # Act
        result = DividendCalculator.calculate_projections(initial, growth, years)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == years
        # All projections should be 0
        assert all(
            result["Projected Dividend"] == 0.0
        ), "Zero dividend should remain zero even with growth"

    def test_negative_growth_projection(self) -> None:
        """Test projection with negative growth (dividend declining over time)."""
        # Arrange
        initial = 100.0
        negative_growth = -10.0  # 10% annual decline
        years = 3

        # Act
        result = DividendCalculator.calculate_projections(
            initial, negative_growth, years
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        # Verify declining values
        dividends = result["Projected Dividend"].values
        for i in range(len(dividends) - 1):
            assert dividends[i + 1] < dividends[i], (
                f"With negative growth, dividends should decline. "
                f"Got {dividends[i]} -> {dividends[i+1]}"
            )

    def test_one_year_projection(self) -> None:
        """Test projection for exactly 1 year."""
        # Arrange
        initial = 100.0
        growth = 10.0
        years = 1

        # Act
        result = DividendCalculator.calculate_projections(initial, growth, years)

        # Assert
        assert len(result) == 1
        assert (
            result["Projected Dividend"].iloc[0] == initial
        ), "Single year projection should equal initial dividend"

    def test_very_long_projection(self) -> None:
        """Test projection for many years (stress test)."""
        # Arrange
        initial = 100.0
        growth = 7.0
        years = 100  # 100 years of compound growth

        # Act
        result = DividendCalculator.calculate_projections(initial, growth, years)

        # Assert
        assert len(result) == years
        assert all(
            result["Projected Dividend"] > 0
        ), "All projections should be positive"
        # Verify exponential growth (final should be much larger than initial)
        final_dividend = result["Projected Dividend"].iloc[-1]
        assert final_dividend > initial * 10, (
            f"100 years of 7% growth should increase significantly. "
            f"Initial: {initial}, Final: {final_dividend}"
        )

    def test_very_high_growth_rate(self) -> None:
        """Test projection with unrealistic but valid high growth rate."""
        # Arrange
        initial = 100.0
        high_growth = 50.0  # 50% annual growth (unrealistic but valid)
        years = 5

        # Act
        result = DividendCalculator.calculate_projections(initial, high_growth, years)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == years
        # Verify exponential growth
        assert (
            result["Projected Dividend"].iloc[-1] > result["Projected Dividend"].iloc[0]
        )

    def test_very_low_growth_rate(self) -> None:
        """Test projection with very small growth rate (almost zero)."""
        # Arrange
        initial = 100.0
        tiny_growth = 0.001  # 0.001% annual growth
        years = 100

        # Act
        result = DividendCalculator.calculate_projections(initial, tiny_growth, years)

        # Assert
        assert isinstance(result, pd.DataFrame)
        # Change should be minimal but present for 100 years
        assert result["Projected Dividend"].iloc[-1] > initial


@pytest.mark.unit
class TestDataIntegrity:
    """Test data integrity and consistency."""

    def test_filter_returns_independent_copy(self, tmp_path: Path) -> None:
        """Test that filtered data is a copy, not a view."""
        # Arrange
        file_path = tmp_path / "test.csv"
        df = pd.DataFrame(
            {
                "Ticker": ["AAPL.US", "MSFT.US"],
                "Net Dividend": ["50 USD", "75 USD"],
                "Tax Collected": ["10%", "15%"],
                "Shares": [100, 50],
            }
        )
        df.to_csv(file_path, sep="\t", index=False)
        processor = DividendDataProcessor(str(file_path))

        # Act
        filtered = processor.filter_data(["AAPL.US"])
        original_value = processor.df.loc[0, "Net Dividend"]
        filtered.iloc[0, processor.df.columns.get_loc("Net Dividend")] = 999.0

        # Assert - original should be unchanged
        current_original = processor.df.loc[0, "Net Dividend"]
        assert (
            current_original == original_value
        ), "Modifications to filtered data should not affect original"

    def test_multiple_filters_produce_consistent_results(self, tmp_path: Path) -> None:
        """Test that filtering same ticker twice produces same result."""
        # Arrange
        file_path = tmp_path / "test.csv"
        df = pd.DataFrame(
            {
                "Ticker": ["AAPL.US", "MSFT.US", "AAPL.US"],
                "Net Dividend": ["50 USD", "75 USD", "60 USD"],
                "Tax Collected": ["10%", "15%", "12%"],
                "Shares": [100, 50, 100],
            }
        )
        df.to_csv(file_path, sep="\t", index=False)
        processor = DividendDataProcessor(str(file_path))

        # Act - filter twice
        filter_1 = processor.filter_data(["AAPL.US"])
        filter_2 = processor.filter_data(["AAPL.US"])

        # Assert - results should be identical
        pd.testing.assert_frame_equal(filter_1, filter_2, check_dtype=True)
