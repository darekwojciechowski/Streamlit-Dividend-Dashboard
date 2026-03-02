"""Unit tests for DividendCalculator utility class.

Tests cover:
- Currency symbol inference from ticker suffixes
- Initial dividend extraction from DataFrames
- Dividend growth projections with compound annual growth rates (CAGR)
- Growth statistics calculations and comparisons

All methods in DividendCalculator are static (@staticmethod), so tests
verify pure function behavior with no instance state dependencies.

Test organization:
- Currency: Symbol lookup by ticker country code
- Initial dividend: Extraction logic and edge cases
- Projections: Year-by-year CAGR calculations
- Growth statistics: Summary calculations and compound growth
- Static methods: Verification of pure function nature
"""

import pytest
import pandas as pd
from datetime import datetime
from app.utils.dividend_calculator import DividendCalculator

# ============================================================================
# TEST CONSTANTS - Reusable test data
# ============================================================================

# Currency tests
TICKER_US = "AAPL.US"
TICKER_POLAND = "PKO.PL"
TICKER_EUROPE = "SAP.EU"
TICKER_UNKNOWN = "UNKNOWN.XX"
TICKER_NO_SUFFIX = "NOTICKER"

CURRENCY_USD = "$"
CURRENCY_PLN = "PLN"
CURRENCY_EUR = "€"

# Growth projection tests
INITIAL_DIVIDEND_100 = 100.0
INITIAL_DIVIDEND_50 = 50.0
INITIAL_DIVIDEND_200 = 200.0

GROWTH_RATE_ZERO = 0.0
GROWTH_RATE_POSITIVE = 7.0
GROWTH_RATE_HIGH = 10.0
GROWTH_RATE_NEGATIVE = -5.0

YEARS_1 = 1
YEARS_2 = 2
YEARS_3 = 3
YEARS_5 = 5
YEARS_10 = 10
YEARS_20 = 20

# Expected values (for verification)
DIVIDEND_100_AFTER_7PCT_1YR = 107.0  # 100 * 1.07
DIVIDEND_100_AFTER_10PCT_2YR = 110.0  # 100 * 1.10


def _assert_projection_structure(result: pd.DataFrame, expected_length: int) -> None:
    """Helper: Verify projection DataFrame has required structure.

    Args:
        result: DataFrame returned from calculate_projections
        expected_length: Expected number of rows

    Raises:
        AssertionError: If structure is invalid
    """
    assert isinstance(result, pd.DataFrame)
    assert len(result) == expected_length
    assert "Year" in result.columns
    assert "Projected Dividend" in result.columns


@pytest.mark.unit
class TestCurrencySymbolInference:
    """Test currency symbol determination from ticker country codes.

    Ticker format: SYMBOL.COUNTRY where COUNTRY determines currency.
    If country is unknown or missing, defaults to USD ($).
    """

    @pytest.mark.parametrize(
        "ticker,expected_currency,country",
        [
            pytest.param(TICKER_US, CURRENCY_USD, "US", id="us-aapl"),
            pytest.param("MSFT.US", CURRENCY_USD, "US (Microsoft)", id="us-msft"),
            pytest.param(TICKER_POLAND, CURRENCY_PLN, "PL (Poland)", id="pln-pko"),
            pytest.param(TICKER_EUROPE, CURRENCY_EUR, "EU (Europe)", id="eur-sap"),
            pytest.param("ORANGE.EU", CURRENCY_EUR, "EU (Europe)", id="eur-orange"),
            pytest.param(
                TICKER_UNKNOWN,
                CURRENCY_USD,
                "Unknown code - default to USD",
                id="unknown-default-usd",
            ),
            pytest.param(
                TICKER_NO_SUFFIX,
                CURRENCY_USD,
                "No suffix - default to USD",
                id="no-suffix-default-usd",
            ),
        ],
    )
    def test_currency_symbol_by_ticker_suffix(
        self, ticker: str, expected_currency: str, country: str
    ) -> None:
        """Test currency inference from ticker country code suffix.

        Args:
            ticker: Ticker symbol (e.g., AAPL.US)
            expected_currency: Expected currency symbol
            country: Country description for documentation
        """
        # Act
        result = DividendCalculator.get_currency_symbol(ticker)

        # Assert
        assert (
            result == expected_currency
        ), f"Failed for {country}: {ticker} - expected {expected_currency}, got {result}"

    def test_get_currency_symbol_callable_as_static_method(self) -> None:
        """Test that get_currency_symbol is truly static (no instance needed).

        Static methods can be called on the class directly without instantiation.
        """
        # Act - call without creating instance
        result = DividendCalculator.get_currency_symbol(TICKER_US)

        # Assert
        assert isinstance(result, str)
        assert result == CURRENCY_USD


@pytest.mark.unit
class TestInitialDividendExtraction:
    """Test extraction of initial (current) dividend from ticker data.

    The get_initial_dividend method finds the first positive non-zero
    dividend value in a DataFrame. Returns None for empty/invalid data.
    """

    def test_extract_first_positive_dividend(self) -> None:
        """Test extraction of first positive dividend value.

        Given multiple dividend values, should return the first one.
        """
        # Arrange
        ticker_data = pd.DataFrame(
            {"Net Dividend": [INITIAL_DIVIDEND_100, 105.0, 110.0]}
        )

        # Act
        result = DividendCalculator.get_initial_dividend(ticker_data)

        # Assert
        assert (
            result == INITIAL_DIVIDEND_100
        ), f"Should extract first dividend value, got {result}"

    def test_extract_returns_none_for_empty_dataframe(self) -> None:
        """Test extraction returns None when DataFrame is empty."""
        # Arrange
        ticker_data = pd.DataFrame()

        # Act
        result = DividendCalculator.get_initial_dividend(ticker_data)

        # Assert
        assert result is None

    def test_extract_returns_none_when_column_missing(self) -> None:
        """Test extraction returns None when required column doesn't exist.

        Must have 'Net Dividend' column to extract initial value.
        """
        # Arrange
        ticker_data = pd.DataFrame({"OtherColumn": [INITIAL_DIVIDEND_100]})

        # Act
        result = DividendCalculator.get_initial_dividend(ticker_data)

        # Assert
        assert result is None

    def test_extract_returns_none_when_all_nan(self) -> None:
        """Test extraction returns None when all values are NaN/missing."""
        # Arrange
        ticker_data = pd.DataFrame({"Net Dividend": [None, None, None]})

        # Act
        result = DividendCalculator.get_initial_dividend(ticker_data)

        # Assert
        assert result is None

    def test_extract_returns_none_for_negative_dividends(self) -> None:
        """Test extraction returns None when all values are negative.

        Negative dividends are invalid (payout cannot be negative).
        """
        # Arrange
        ticker_data = pd.DataFrame({"Net Dividend": [-10.0, -5.0]})

        # Act
        result = DividendCalculator.get_initial_dividend(ticker_data)

        # Assert
        assert result is None

    def test_extract_returns_none_for_zero_dividend(self) -> None:
        """Test extraction returns None when first value is zero.

        Zero dividend is not a valid initial state (no payout).
        """
        # Arrange
        ticker_data = pd.DataFrame({"Net Dividend": [0.0, INITIAL_DIVIDEND_100]})

        # Act
        result = DividendCalculator.get_initial_dividend(ticker_data)

        # Assert
        assert result is None

    def test_extract_skips_nan_finds_first_positive(self) -> None:
        """Test extraction skips NaN values and returns first positive.

        Should scan past None/NaN values to find first valid dividend.
        """
        # Arrange
        ticker_data = pd.DataFrame(
            {"Net Dividend": [None, None, INITIAL_DIVIDEND_50, 55.0]}
        )

        # Act
        result = DividendCalculator.get_initial_dividend(ticker_data)

        # Assert
        assert result == INITIAL_DIVIDEND_50


@pytest.mark.unit
class TestDividendProjections:
    """Test dividend projection with compound annual growth rate (CAGR).

    calculate_projections generates year-by-year forecasts using:
    Future_Dividend = Initial * (1 + Growth Rate)^Years

    Results include both Year and Projected Dividend columns.
    """

    def test_calculate_basic_cagr_projection(self) -> None:
        """Test basic CAGR projection calculation.

        With 7% annual growth over 5 years:
        Year 1: 100 * 1.07^0 = 100.0
        Year 2: 100 * 1.07^1 = 107.0
        Year 3: 100 * 1.07^2 = 114.49
        """
        # Arrange
        initial = INITIAL_DIVIDEND_100
        growth_rate = GROWTH_RATE_POSITIVE
        years = YEARS_5

        # Act
        result = DividendCalculator.calculate_projections(initial, growth_rate, years)

        # Assert
        _assert_projection_structure(result, YEARS_5)
        # Year 1 (index 0): Initial dividend unchanged
        assert result["Projected Dividend"].iloc[0] == pytest.approx(initial)
        # Year 2 (index 1): 100 * 1.07 = 107
        assert result["Projected Dividend"].iloc[1] == pytest.approx(
            DIVIDEND_100_AFTER_7PCT_1YR
        )

    def test_flat_projection_with_zero_growth(self) -> None:
        """Test projection with 0% growth rate stays flat.

        With zero growth, dividend never changes across years.
        """
        # Arrange
        initial = INITIAL_DIVIDEND_100
        growth_rate = GROWTH_RATE_ZERO
        years = YEARS_3

        # Act
        result = DividendCalculator.calculate_projections(initial, growth_rate, years)

        # Assert
        assert len(result) == YEARS_3
        # All years should have same dividend
        assert all(result["Projected Dividend"] == initial)

    def test_declining_projection_with_negative_growth(self) -> None:
        """Test projection with negative growth shows dividend decline.

        With -5% annual decline:
        Year 1: 100.0
        Year 2: 100 * 0.95 = 95.0
        """
        # Arrange
        initial = INITIAL_DIVIDEND_100
        growth_rate = GROWTH_RATE_NEGATIVE
        years = YEARS_2

        # Act
        result = DividendCalculator.calculate_projections(initial, growth_rate, years)

        # Assert
        assert result["Projected Dividend"].iloc[0] == initial
        assert result["Projected Dividend"].iloc[1] == pytest.approx(95.0)

    def test_projection_years_are_sequential_dates(self) -> None:
        """Test that projected years are consecutive calendar years.

        Years should start from current year and increment: 2026, 2027, 2028, ...
        """
        # Arrange
        initial = INITIAL_DIVIDEND_100
        growth_rate = GROWTH_RATE_POSITIVE
        years = YEARS_3

        # Act
        result = DividendCalculator.calculate_projections(initial, growth_rate, years)

        # Assert
        current_year = datetime.now().year
        expected_years = [current_year, current_year + 1, current_year + 2]
        assert result["Year"].tolist() == expected_years

    def test_single_year_projection(self) -> None:
        """Test projection for just one year returns that year's data."""
        # Arrange
        initial = INITIAL_DIVIDEND_50
        growth_rate = GROWTH_RATE_HIGH
        years = YEARS_1

        # Act
        result = DividendCalculator.calculate_projections(initial, growth_rate, years)

        # Assert
        assert len(result) == YEARS_1
        # Year 1 dividend equals initial (no growth applied in year 1)
        assert result["Projected Dividend"].iloc[0] == initial

    @pytest.mark.parametrize(
        "initial,growth,years,description",
        [
            pytest.param(
                INITIAL_DIVIDEND_100,
                5.0,
                YEARS_10,
                "10-year moderate growth",
                id="10yr-5pct",
            ),
            pytest.param(
                INITIAL_DIVIDEND_50,
                7.0,
                YEARS_20,
                "20-year moderate growth",
                id="20yr-7pct",
            ),
            pytest.param(
                INITIAL_DIVIDEND_200, 3.0, YEARS_5, "5-year slow growth", id="5yr-3pct"
            ),
        ],
    )
    def test_projections_various_scenarios(
        self,
        initial: float,
        growth: float,
        years: int,
        description: str,
    ) -> None:
        """Test projections with various realistic scenarios.

        Args:
            initial: Starting dividend amount
            growth: Annual growth rate (%)
            years: Number of years to project
            description: Scenario description
        """
        # Act
        result = DividendCalculator.calculate_projections(initial, growth, years)

        # Assert
        _assert_projection_structure(result, years)
        # First year should equal initial
        assert (
            result["Projected Dividend"].iloc[0] == initial
        ), f"Year 1 projection should equal initial ({initial}), got {result['Projected Dividend'].iloc[0]}"


@pytest.mark.unit
class TestGrowthStatistics:
    """Test growth summary statistics calculations.

    calculate_growth_info computes aggregate statistics for a growth scenario:
    - final_dividend: Projected dividend after N years with growth applied
    - total_increase: Absolute increase (final - initial)
    - total_growth_pct: Percentage increase over period
    - years: Number of years in projection
    """

    def test_calculate_growth_info_structure(self) -> None:
        """Test that growth info returns correct structure (dict with keys)."""
        # Arrange
        initial = INITIAL_DIVIDEND_100
        growth_rate = GROWTH_RATE_POSITIVE
        years = YEARS_5

        # Act
        result = DividendCalculator.calculate_growth_info(initial, growth_rate, years)

        # Assert
        assert isinstance(result, dict)
        assert "final_dividend" in result
        assert "total_growth_pct" in result
        assert "total_increase" in result
        assert "years" in result
        assert result["years"] == YEARS_5

    def test_calculate_growth_info_correct_values(self) -> None:
        """Test growth statistics calculations with known values.

        10% growth over 2 years:
        - Final: 100 * 1.10^2 = 121.0
        - Year 1 dividend: 100 * 1.10 = 110.0
        - Actually: 100 * (1.10^2 - 1) = 21% total growth
        """
        # Arrange
        initial = INITIAL_DIVIDEND_100
        growth_rate = GROWTH_RATE_HIGH
        years = YEARS_2

        # Act
        result = DividendCalculator.calculate_growth_info(initial, growth_rate, years)

        # Assert
        assert result["final_dividend"] == pytest.approx(DIVIDEND_100_AFTER_10PCT_2YR)
        assert result["total_increase"] == pytest.approx(10.0)
        assert result["total_growth_pct"] == pytest.approx(10.0)

    def test_zero_growth_shows_no_increase(self) -> None:
        """Test that 0% growth results in no change in dividend.

        With zero growth, no matter how many years:
        - Final dividend = initial dividend
        - Total increase = 0
        - Total growth % = 0%
        """
        # Arrange
        initial = INITIAL_DIVIDEND_100
        growth_rate = GROWTH_RATE_ZERO
        years = YEARS_5

        # Act
        result = DividendCalculator.calculate_growth_info(initial, growth_rate, years)

        # Assert
        assert result["final_dividend"] == initial
        assert result["total_increase"] == 0.0
        assert result["total_growth_pct"] == 0.0

    def test_negative_growth_shows_decline(self) -> None:
        """Test that negative growth shows dividend decline.

        -10% annual decline over 2 years:
        - Year 1: 100 * 0.90 = 90.0
        - Total Decrease: -10.0
        - Growth %: -10.0%
        """
        # Arrange
        initial = INITIAL_DIVIDEND_100
        growth_rate = -10.0
        years = YEARS_2

        # Act
        result = DividendCalculator.calculate_growth_info(initial, growth_rate, years)

        # Assert
        assert result["final_dividend"] == pytest.approx(90.0)
        assert result["total_increase"] < 0  # Negative increase (decline)
        assert result["total_growth_pct"] < 0  # Negative percentage

    def test_single_year_growth_calculation(self) -> None:
        """Test growth statistics for single year horizon.

        With single year, Year 0 calculation (no growth applied yet):
        - Final dividend = initial (first year own dividend)
        - Total growth = 0%
        """
        # Arrange
        initial = INITIAL_DIVIDEND_50
        growth_rate = GROWTH_RATE_HIGH
        years = YEARS_1

        # Act
        result = DividendCalculator.calculate_growth_info(initial, growth_rate, years)

        # Assert
        # Year 1 uses initial dividend (no growth applied in first year)
        assert result["final_dividend"] == initial
        assert result["total_growth_pct"] == 0.0

    @pytest.mark.parametrize(
        "initial,growth,years,description",
        [
            (INITIAL_DIVIDEND_100, 5.0, YEARS_10, "10-year slow growth"),
            (INITIAL_DIVIDEND_50, 7.0, YEARS_20, "20-year moderate growth"),
            (INITIAL_DIVIDEND_200, -3.0, YEARS_5, "5-year decline"),
        ],
    )
    def test_growth_info_various_scenarios(
        self,
        initial: float,
        growth: float,
        years: int,
        description: str,
    ) -> None:
        """Test growth statistics with various realistic scenarios.

        Args:
            initial: Starting dividend amount
            growth: Annual growth rate (%)
            years: Number of years
            description: Scenario description
        """
        # Act
        result = DividendCalculator.calculate_growth_info(initial, growth, years)

        # Assert
        assert result["years"] == years
        assert isinstance(result["final_dividend"], (int, float))
        assert isinstance(result["total_growth_pct"], (int, float))
        assert isinstance(result["total_increase"], (int, float))


@pytest.mark.unit
class TestStaticMethodProperties:
    """Test that DividendCalculator has pure static methods (no state)."""

    def test_all_methods_are_static(self) -> None:
        """Test static methods work when called on instance.

        Even though methods are @staticmethod, Python allows calling
        them on instances. This test verifies that works.
        """
        # Arrange - create an instance (even though not needed)
        calculator = DividendCalculator()

        # Act - call static method on instance
        result = calculator.get_currency_symbol(TICKER_US)

        # Assert
        assert isinstance(result, str)
        assert result == CURRENCY_USD

    def test_multiple_instances_independent_calculations(self) -> None:
        """Test that different instances produce identical results.

        Since methods are static, there's no instance state. Multiple
        instances should all produce the same output for same inputs.
        """
        # Arrange - create two instances
        calc1 = DividendCalculator()
        calc2 = DividendCalculator()

        # Act - same calculation on both instances
        result1 = calc1.calculate_projections(
            INITIAL_DIVIDEND_100, GROWTH_RATE_POSITIVE, YEARS_3
        )
        result2 = calc2.calculate_projections(
            INITIAL_DIVIDEND_100, GROWTH_RATE_POSITIVE, YEARS_3
        )

        # Assert
        assert result1.equals(result2), "Results should be identical"
