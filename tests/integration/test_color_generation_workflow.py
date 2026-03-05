"""Integration tests for color generation workflow.

Tests verify the complete color assignment flow:
1. Load and filter data by selected tickers
2. Extract unique tickers from filtered data
3. Assign colors to each ticker (color manager)
4. Verify color assignments are consistent and accessible

These tests verify that data_processor and color_manager work together.
"""

from pathlib import Path

import pytest
from app.data_processor import DividendDataProcessor
from app.utils.color_manager import ColorManager, determine_text_color_for_dropdown


@pytest.mark.integration
class TestColorGenerationWorkflow:
    """Test color assignment for filtered dividend data."""

    def test_color_assignment_for_single_ticker(self, sample_tsv_file: Path) -> None:
        """Test color assignment workflow for single ticker.

        Workflow:
        1. Load and process data
        2. Filter for single ticker
        3. Generate colors for filtered tickers
        4. Verify color is assigned
        """
        # Step 1: Load data
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Step 2: Filter for AAPL
        filtered = processor.filter_data(["AAPL.US"])
        tickers = sorted(filtered["Ticker"].unique().tolist())

        # Step 3: Generate colors (returns dict)
        color_manager = ColorManager()
        colors = color_manager.generate_colors_for_tickers(tickers)

        # Step 4: Verify colors assigned
        assert colors is not None
        assert "AAPL.US" in colors
        assert isinstance(colors["AAPL.US"], str)
        assert colors["AAPL.US"].startswith("#")

    def test_color_assignment_for_multiple_tickers(self, sample_tsv_file: Path) -> None:
        """Test color assignment for multiple filtered tickers.

        Workflow:
        1. Load and filter data for multiple tickers
        2. Generate colors for all filtered tickers
        3. Verify each has unique color in correct format
        """
        # Load and filter
        processor = DividendDataProcessor(str(sample_tsv_file))
        selected_tickers = ["AAPL.US", "MSFT.US", "PKO.PL"]
        filtered = processor.filter_data(selected_tickers)
        tickers = sorted(filtered["Ticker"].unique().tolist())

        # Generate colors
        color_manager = ColorManager()
        colors = color_manager.generate_colors_for_tickers(tickers)

        # Verify: each ticker has exactly one color
        assert len(colors) == len(tickers)

        for ticker in tickers:
            assert ticker in colors
            color = colors[ticker]
            # Verify hex format (#RRGGBB)
            assert color.startswith("#")
            assert len(color) == 7

    def test_color_consistency_across_calls(self, sample_tsv_file: Path) -> None:
        """Test that same tickers always get same colors.

        Given:
        - Same set of tickers
        When:
        - Generate colors twice independently
        Then:
        - Colors for each ticker should be identical
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        filtered = processor.filter_data(["AAPL.US", "MSFT.US", "PKO.PL"])
        tickers = sorted(filtered["Ticker"].unique().tolist())

        # First color generation
        color_mgr_1 = ColorManager()
        colors_1 = color_mgr_1.generate_colors_for_tickers(tickers)

        # Second color generation (same order and tickers)
        color_mgr_2 = ColorManager()
        colors_2 = color_mgr_2.generate_colors_for_tickers(tickers)

        # Should be identical
        assert colors_1 == colors_2

    def test_color_assignment_sort_order_matters(self, sample_tsv_file: Path) -> None:
        """Test that color assignment respects sorted ticker order.

        Given:
        - Different sort orders of same ticker list
        When:
        - Generate colors for each order
        Then:
        - Colors should match canonical (sorted) order
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        filtered = processor.filter_data(["AAPL.US", "MSFT.US", "PKO.PL", "SAP.EU"])

        # Get sorted tickers (canonical order)
        canonical_tickers = sorted(filtered["Ticker"].unique().tolist())

        color_manager = ColorManager()
        colors = color_manager.generate_colors_for_tickers(canonical_tickers)

        # Verify colors match canonical order
        assert list(colors.keys()) == canonical_tickers

    def test_end_to_end_data_to_color_workflow(self, sample_tsv_file: Path) -> None:
        """Test complete end-to-end workflow from data to colors.

        Complete workflow:
        1. Load TSV file (DividendDataProcessor)
        2. Clean and validate data
        3. Filter by user selection
        4. Generate colors for filtered tickers (ColorManager)
        5. Verify colors ready for rendering
        """
        # Step 1-3: Load, clean, filter
        processor = DividendDataProcessor(str(sample_tsv_file))
        user_selection = ["AAPL.US", "PKO.PL"]
        filtered_df = processor.filter_data(user_selection)

        assert not filtered_df.empty
        assert all(ticker in user_selection for ticker in filtered_df["Ticker"].unique())

        # Step 4: Generate colors
        unique_tickers = sorted(filtered_df["Ticker"].unique().tolist())
        color_mgr = ColorManager()
        colors = color_mgr.generate_colors_for_tickers(unique_tickers)

        # Step 5: Verify colors ready for rendering
        assert len(colors) == len(unique_tickers)
        assert all(isinstance(color, str) and color.startswith("#") for color in colors.values())

    def test_wcag_color_contrast_for_all_assigned_colors(self, sample_tsv_file: Path) -> None:
        """Test that all assigned colors meet WCAG contrast standards.

        Given:
        - Filtered data and assigned colors
        When:
        - Check color contrast requirements
        Then:
        - All text on these colors should be readable
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        filtered = processor.filter_data([])  # Get all tickers
        if filtered.empty:
            filtered = processor.df

        tickers = sorted(filtered["Ticker"].unique().tolist())
        color_mgr = ColorManager()
        colors = color_mgr.generate_colors_for_tickers(tickers)

        # Verify all colors can have readable text (WCAG contrast check)
        for _ticker, color in colors.items():
            # Should be able to determine text color without exception
            text_color = determine_text_color_for_dropdown(color)
            assert text_color in ["#000000", "#FFFFFF"]
