"""Integration tests for dividend calculation workflow.

Tests verify the complete dividend calculation flow:
1. Load and filter dividend data
2. Extract initial dividends by ticker
3. Project future dividend income using CAGR
4. Calculate dividend growth statistics

These tests verify that data_processor and dividend_calculator work together.
"""

import pytest
import pandas as pd
from pathlib import Path

from app.data_processor import DividendDataProcessor
from app.utils.dividend_calculator import DividendCalculator


@pytest.mark.integration
class TestDividendCalculationWorkflow:
    """Test complete dividend calculation workflows."""

    def test_extract_and_project_dividends(self, sample_tsv_file: Path) -> None:
        """Test extracting initial dividends and projecting future income.

        Workflow:
        1. Load and filter data
        2. Extract initial dividend for a ticker
        3. Project future dividend with CAGR using calculate_projections
        4. Verify projection increases over time
        """
        # Step 1: Load and filter
        processor = DividendDataProcessor(str(sample_tsv_file))
        filtered = processor.filter_data(["AAPL.US"])

        # Step 2: Extract initial dividend (sum all AAPL dividends)
        initial = filtered["Net Dividend"].sum()
        assert initial > 0

        # Step 3: Project with 7% growth for 5 years
        calculator = DividendCalculator()
        cagr = 7.0
        years = 5

        # Get projections DataFrame
        projections_df = calculator.calculate_projections(initial, cagr, years)
        assert projections_df is not None
        assert not projections_df.empty
        assert len(projections_df) == years

        # Step 4: Verify growth - first year equals initial, final year shows growth
        year_1_dividend = projections_df.iloc[0]["Projected Dividend"]
        year_5_dividend = projections_df.iloc[years - 1]["Projected Dividend"]

        assert year_1_dividend == pytest.approx(initial)
        assert year_5_dividend > year_1_dividend
        assert year_5_dividend > initial

    def test_dividend_currency_detection_from_filtered_data(
        self, sample_tsv_file: Path
    ) -> None:
        """Test currency symbol inference from filtered ticker data.

        Workflow:
        1. Load and filter data to single ticker
        2. Get ticker symbol from filtered data
        3. Infer currency from ticker suffix
        4. Verify correct symbol returned
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Filter US ticker
        filtered_us = processor.filter_data(["AAPL.US"])
        ticker_us = filtered_us["Ticker"].iloc[0]
        assert ticker_us == "AAPL.US"

        calculator = DividendCalculator()
        currency_us = calculator.get_currency_symbol(ticker_us)
        assert currency_us == "$"

        # Filter Poland ticker
        filtered_pl = processor.filter_data(["PKO.PL"])
        ticker_pl = filtered_pl["Ticker"].iloc[0]
        assert ticker_pl == "PKO.PL"

        currency_pl = calculator.get_currency_symbol(ticker_pl)
        assert currency_pl == "PLN"

    def test_total_annual_dividend_calculation(self, sample_tsv_file: Path) -> None:
        """Test calculating total annual dividend from filtered data.

        Workflow:
        1. Load and filter data for multiple tickers
        2. Sum dividends across all tickers
        3. Verify aggregation is correct
        """
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Filter for all tickers
        filtered = processor.filter_data(["AAPL.US", "MSFT.US", "PKO.PL"])

        total_dividend = filtered["Net Dividend"].sum()
        assert total_dividend > 0

        # Verify we can calculate projections on total
        calculator = DividendCalculator()
        projections_df = calculator.calculate_projections(total_dividend, 7.0, 5)

        # Get 5-year projection
        if not projections_df.empty:
            projected_5yr = projections_df.iloc[-1]["Projected Dividend"]
            assert projected_5yr > total_dividend

    def test_growth_statistics_for_filtered_portfolio(
        self, sample_tsv_file: Path
    ) -> None:
        """Test calculating growth statistics for filtered ticker set.

        Workflow:
        1. Load and filter data
        2. Calculate initial total dividend
        3. Generate growth projections for 5 years
        4. Verify growth statistics increase monotonically
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        filtered = processor.filter_data(["AAPL.US", "MSFT.US"])

        initial = filtered["Net Dividend"].sum()
        calculator = DividendCalculator()

        # Generate projections
        projections_df = calculator.calculate_projections(initial, 7.0, 5)

        assert projections_df is not None
        assert not projections_df.empty

        # Verify growth increases monotonically (year 1 = initial, then grows)
        prev_value = initial - 0.01  # Set slightly below initial for first comparison
        for _, row in projections_df.iterrows():
            current = row["Projected Dividend"]
            assert current >= prev_value
            prev_value = current

    def test_cagr_impact_on_dividend_growth(self, sample_tsv_file: Path) -> None:
        """Test that higher CAGR produces higher future dividends.

        Workflow:
        1. Load and filter data
        2. Extract initial dividend
        3. Project with multiple CAGR rates (3%, 7%, 10%)
        4. Verify higher CAGR gives higher projections
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        filtered = processor.filter_data(["MSFT.US"])
        initial = filtered["Net Dividend"].sum()

        calculator = DividendCalculator()
        years = 5

        # Project with different CAGR rates - get the final year value
        low_df = calculator.calculate_projections(initial, 3.0, years)
        med_df = calculator.calculate_projections(initial, 7.0, years)
        high_df = calculator.calculate_projections(initial, 10.0, years)

        low_growth = low_df.iloc[-1]["Projected Dividend"]
        med_growth = med_df.iloc[-1]["Projected Dividend"]
        high_growth = high_df.iloc[-1]["Projected Dividend"]

        # Verify expected ordering
        assert low_growth < med_growth < high_growth

    def test_zero_cagr_maintains_constant_dividend(self, sample_tsv_file: Path) -> None:
        """Test that 0% CAGR keeps dividend constant over time.

        Workflow:
        1. Load and filter data
        2. Extract initial dividend
        3. Project with 0% CAGR for multiple years
        4. Verify dividend remains constant
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        filtered = processor.filter_data(["AAPL.US"])
        initial = filtered["Net Dividend"].sum()

        calculator = DividendCalculator()

        # Project with 0% growth for different year lengths
        df_1yr = calculator.calculate_projections(initial, 0.0, 1)
        df_5yr = calculator.calculate_projections(initial, 0.0, 5)
        df_10yr = calculator.calculate_projections(initial, 0.0, 10)

        year_1 = df_1yr.iloc[-1]["Projected Dividend"]
        year_5 = df_5yr.iloc[-1]["Projected Dividend"]
        year_10 = df_10yr.iloc[-1]["Projected Dividend"]

        # All should equal initial (approximately, due to floating point)
        assert abs(year_1 - initial) < 0.01
        assert abs(year_5 - initial) < 0.01
        assert abs(year_10 - initial) < 0.01

    def test_complete_end_to_end_dividend_workflow(self, sample_tsv_file: Path) -> None:
        """Test complete end-to-end dividend calculation workflow.

        Complete workflow:
        1. Load data
        2. User selects tickers to analyze
        3. Filter data for selection
        4. Calculate total current dividend
        5. Project future dividend income
        6. Calculate growth over time
        """
        # Step 1: Load
        processor = DividendDataProcessor(str(sample_tsv_file))

        # Step 2-3: User selects tickers
        user_tickers = ["AAPL.US", "PKO.PL", "SAP.EU"]
        filtered = processor.filter_data(user_tickers)

        assert not filtered.empty
        assert all(t in user_tickers for t in filtered["Ticker"].unique())

        # Step 4: Calculate current annual dividend
        current_annual = filtered["Net Dividend"].sum()
        assert current_annual > 0

        # Step 5-6: Project growth
        calculator = DividendCalculator()
        cagr = 6.5

        # Calculate projections for different years
        proj_1yr = calculator.calculate_projections(current_annual, cagr, 1)
        proj_5yr = calculator.calculate_projections(current_annual, cagr, 5)
        proj_10yr = calculator.calculate_projections(current_annual, cagr, 10)
        proj_20yr = calculator.calculate_projections(current_annual, cagr, 20)

        # Extract end values
        projections = {
            1: proj_1yr.iloc[-1]["Projected Dividend"],
            5: proj_5yr.iloc[-1]["Projected Dividend"],
            10: proj_10yr.iloc[-1]["Projected Dividend"],
            20: proj_20yr.iloc[-1]["Projected Dividend"],
        }

        # Verify projections are increasing (year 1 = current_annual, then grows)
        assert projections[1] == pytest.approx(current_annual)
        assert projections[5] > projections[1]
        assert projections[10] > projections[5]
        assert projections[20] > projections[10]

        # 20-year projection with 6.5% CAGR should roughly double or more
        assert projections[20] > current_annual * 1.5

    def test_per_ticker_dividend_projection(self, sample_tsv_file: Path) -> None:
        """Test calculating projections for individual tickers.

        Workflow:
        1. Load and filter data
        2. For each ticker, calculate its dividend
        3. Project each ticker's dividend independently
        4. Verify all projections are consistent
        """
        processor = DividendDataProcessor(str(sample_tsv_file))
        calculator = DividendCalculator()

        tickers = ["AAPL.US", "MSFT.US", "PKO.PL"]
        projections_by_ticker = {}

        for ticker in tickers:
            filtered = processor.filter_data([ticker])
            if not filtered.empty:
                current_div = filtered["Net Dividend"].sum()
                proj_df = calculator.calculate_projections(current_div, 7.0, 5)

                if not proj_df.empty:
                    projected_5yr = proj_df.iloc[-1]["Projected Dividend"]
                    projections_by_ticker[ticker] = {
                        "current": current_div,
                        "projected_5yr": projected_5yr,
                    }

                    # Verify each projection makes sense
                    assert projections_by_ticker[ticker]["projected_5yr"] > current_div

        # Verify we got projections for all tickers
        assert len(projections_by_ticker) == len(tickers)
