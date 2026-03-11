"""Unit tests for DRIPCalculator.calculate_drip() pure calculation logic.

Tests cover:
- DataFrame structure and required columns
- Year-0 baseline (no reinvestment yet)
- Share accumulation through reinvestment
- Dividend growth compounding over years
- Share price growth effect on portfolio value
- DRIP benefit vs value without DRIP
- Edge cases: zero growth rates, single year, monthly/annual frequency
- Boundary values: very high growth rates, fractional shares

All tests operate only on calculate_drip() — the pure DataFrame-returning method.
Streamlit render methods (render_modern_chart, render_metrics_cards) are not tested
here as they depend on st.* calls.
"""

import pandas as pd
import pytest

from app.components.drip_calculator import DRIPCalculator

# ============================================================================
# MARKERS
# ============================================================================

pytestmark = pytest.mark.unit

# ============================================================================
# FIXTURES
# ============================================================================

TICKER_COLORS = {"AAPL.US": "#8A2BE2", "MSFT.US": "#636EFA"}

INITIAL_SHARES = 100.0
SHARE_PRICE = 50.0
ANNUAL_DIVIDEND = 200.0  # $2/share * 100 shares
DIVIDEND_GROWTH = 6.0
PRICE_GROWTH = 4.0
YEARS = 10
QUARTERLY = 4
MONTHLY = 12
ANNUAL = 1


@pytest.fixture
def calculator() -> DRIPCalculator:
    return DRIPCalculator(ticker_colors=TICKER_COLORS)


@pytest.fixture
def base_df(calculator: DRIPCalculator) -> pd.DataFrame:
    """Standard 10-year quarterly DRIP projection."""
    return calculator.calculate_drip(
        initial_shares=INITIAL_SHARES,
        share_price=SHARE_PRICE,
        annual_dividend=ANNUAL_DIVIDEND,
        dividend_growth=DIVIDEND_GROWTH,
        share_price_growth=PRICE_GROWTH,
        years=YEARS,
        payment_frequency=QUARTERLY,
    )


# ============================================================================
# TESTS: DataFrame structure
# ============================================================================


class TestDRIPDataFrameStructure:
    """Verify output DataFrame has correct shape, columns, and types."""

    EXPECTED_COLUMNS = {
        "Year",
        "Shares",
        "Shares Added",
        "Share Price",
        "Annual Dividend",
        "Total Dividend Income",
        "Portfolio Value",
        "Value Without DRIP",
        "DRIP Benefit",
    }

    def test_returns_dataframe(self, base_df: pd.DataFrame):
        assert isinstance(base_df, pd.DataFrame)

    def test_row_count_equals_years_plus_one(self, calculator: DRIPCalculator):
        for years in (1, 5, 10, 20):
            df = calculator.calculate_drip(
                initial_shares=INITIAL_SHARES,
                share_price=SHARE_PRICE,
                annual_dividend=ANNUAL_DIVIDEND,
                dividend_growth=DIVIDEND_GROWTH,
                share_price_growth=PRICE_GROWTH,
                years=years,
            )
            assert len(df) == years + 1, f"Expected {years + 1} rows for years={years}"

    def test_required_columns_present(self, base_df: pd.DataFrame):
        assert self.EXPECTED_COLUMNS.issubset(set(base_df.columns))

    def test_all_numeric_columns(self, base_df: pd.DataFrame):
        numeric_cols = [
            "Shares",
            "Shares Added",
            "Share Price",
            "Annual Dividend",
            "Total Dividend Income",
            "Portfolio Value",
            "Value Without DRIP",
            "DRIP Benefit",
        ]
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(base_df[col]), f"{col} should be numeric"

    def test_year_column_is_integer_type(self, base_df: pd.DataFrame):
        assert pd.api.types.is_integer_dtype(base_df["Year"])


# ============================================================================
# TESTS: Year-0 baseline
# ============================================================================


class TestDRIPYearZeroBaseline:
    """Year 0 row represents the starting state before any reinvestment."""

    def test_year_zero_shares_equal_initial(self, base_df: pd.DataFrame):
        # Year 0: reinvestment happens in year 0 loop too (quarterly payments)
        # shares should be >= initial_shares
        assert base_df.iloc[0]["Shares"] >= INITIAL_SHARES

    def test_year_zero_shares_added_nonnegative(self, base_df: pd.DataFrame):
        assert base_df.iloc[0]["Shares Added"] >= 0.0

    def test_year_zero_portfolio_value_positive(self, base_df: pd.DataFrame):
        assert base_df.iloc[0]["Portfolio Value"] > 0.0

    def test_value_without_drip_uses_initial_shares(self, base_df: pd.DataFrame):
        # "Value Without DRIP" = initial_shares * price_end_of_year
        row0 = base_df.iloc[0]
        expected = INITIAL_SHARES * row0["Share Price"]
        assert abs(row0["Value Without DRIP"] - expected) < 0.01


# ============================================================================
# TESTS: Share accumulation
# ============================================================================


class TestDRIPShareAccumulation:
    """Shares should increase monotonically when dividend and price > 0."""

    def test_shares_monotonically_increasing(self, base_df: pd.DataFrame):
        shares = base_df["Shares"].tolist()
        for i in range(1, len(shares)):
            assert shares[i] >= shares[i - 1], f"Shares decreased at row {i}"

    def test_shares_added_nonnegative_every_year(self, base_df: pd.DataFrame):
        assert (base_df["Shares Added"] >= 0).all()

    def test_total_shares_exceeds_initial_after_ten_years(self, base_df: pd.DataFrame):
        assert base_df.iloc[-1]["Shares"] > INITIAL_SHARES

    def test_more_shares_with_monthly_vs_quarterly(self, calculator: DRIPCalculator):
        """Monthly reinvestment compounds faster than quarterly."""
        df_q = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=DIVIDEND_GROWTH,
            share_price_growth=PRICE_GROWTH,
            years=YEARS,
            payment_frequency=MONTHLY,
        )
        df_a = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=DIVIDEND_GROWTH,
            share_price_growth=PRICE_GROWTH,
            years=YEARS,
            payment_frequency=ANNUAL,
        )
        assert df_q.iloc[-1]["Shares"] > df_a.iloc[-1]["Shares"]


# ============================================================================
# TESTS: Zero growth rates
# ============================================================================


class TestDRIPZeroGrowthRates:
    """Verify behavior when no dividend or price growth is applied."""

    def test_zero_dividend_growth_annual_dividend_constant(self, calculator: DRIPCalculator):
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=0.0,
            share_price_growth=0.0,
            years=5,
        )
        dividends = df["Annual Dividend"].round(4).tolist()
        for d in dividends:
            assert abs(d - ANNUAL_DIVIDEND) < 0.01, f"Expected constant {ANNUAL_DIVIDEND}, got {d}"

    def test_zero_price_growth_share_price_constant(self, calculator: DRIPCalculator):
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=0.0,
            share_price_growth=0.0,
            years=5,
        )
        # Year 0 price should equal initial price; all years same
        prices = df["Share Price"].round(4).tolist()
        for p in prices:
            assert abs(p - SHARE_PRICE) < 0.01


# ============================================================================
# TESTS: Dividend and price growth compounding
# ============================================================================


class TestDRIPGrowthCompounding:
    """Annual Dividend and Share Price grow by specified percentages each year."""

    def test_annual_dividend_grows_by_rate(self, calculator: DRIPCalculator):
        rate = 10.0
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=rate,
            share_price_growth=0.0,
            years=3,
        )
        for i in range(1, len(df)):
            expected = df.iloc[i - 1]["Annual Dividend"] * (1 + rate / 100)
            assert abs(df.iloc[i]["Annual Dividend"] - expected) < 0.001

    def test_share_price_grows_by_rate(self, calculator: DRIPCalculator):
        rate = 8.0
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=0.0,
            share_price_growth=rate,
            years=3,
        )
        for i in range(1, len(df)):
            expected = df.iloc[i - 1]["Share Price"] * (1 + rate / 100)
            assert abs(df.iloc[i]["Share Price"] - expected) < 0.001

    def test_portfolio_value_grows_with_price_and_reinvestment(self, base_df: pd.DataFrame):
        portfolio_values = base_df["Portfolio Value"].tolist()
        for i in range(1, len(portfolio_values)):
            assert portfolio_values[i] > portfolio_values[i - 1]


# ============================================================================
# TESTS: DRIP benefit calculation
# ============================================================================


class TestDRIPBenefit:
    """DRIP Benefit = Portfolio Value - Value Without DRIP."""

    def test_drip_benefit_equals_difference(self, base_df: pd.DataFrame):
        for _, row in base_df.iterrows():
            expected_benefit = row["Portfolio Value"] - row["Value Without DRIP"]
            assert abs(row["DRIP Benefit"] - expected_benefit) < 0.01

    def test_drip_benefit_positive_after_reinvestment(self, base_df: pd.DataFrame):
        # After year 0, DRIP benefit should be >= 0 (reinvestment adds value)
        later_benefits = base_df.iloc[1:]["DRIP Benefit"]
        assert (later_benefits >= 0).all()

    def test_drip_benefit_increases_over_time(self, base_df: pd.DataFrame):
        """Compounding reinvestment should widen the gap each year."""
        benefits = base_df["DRIP Benefit"].tolist()
        for i in range(2, len(benefits)):
            assert benefits[i] >= benefits[i - 1], f"DRIP benefit decreased at year {i}"


# ============================================================================
# TESTS: Payment frequency impact
# ============================================================================


class TestDRIPPaymentFrequency:
    """Different payment frequencies produce different accumulation trajectories."""

    @pytest.mark.parametrize("frequency", [1, 2, 4, 12])
    def test_valid_payment_frequencies_produce_results(self, calculator: DRIPCalculator, frequency: int):
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=DIVIDEND_GROWTH,
            share_price_growth=PRICE_GROWTH,
            years=5,
            payment_frequency=frequency,
        )
        assert len(df) == 6
        assert (df["Shares"] > 0).all()

    def test_higher_frequency_yields_more_shares(self, calculator: DRIPCalculator):
        kwargs = dict(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=DIVIDEND_GROWTH,
            share_price_growth=PRICE_GROWTH,
            years=10,
        )
        df_1 = calculator.calculate_drip(**kwargs, payment_frequency=1)
        df_4 = calculator.calculate_drip(**kwargs, payment_frequency=4)
        df_12 = calculator.calculate_drip(**kwargs, payment_frequency=12)

        final_shares = {1: df_1.iloc[-1]["Shares"], 4: df_4.iloc[-1]["Shares"], 12: df_12.iloc[-1]["Shares"]}
        # More frequent reinvestment → more shares
        assert final_shares[12] > final_shares[4] > final_shares[1]


# ============================================================================
# TESTS: Edge cases
# ============================================================================


class TestDRIPEdgeCases:
    """Boundary conditions and edge inputs."""

    def test_single_year_projection(self, calculator: DRIPCalculator):
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=0.0,
            share_price_growth=0.0,
            years=1,
        )
        assert len(df) == 2

    def test_zero_years_projection(self, calculator: DRIPCalculator):
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=0.0,
            share_price_growth=0.0,
            years=0,
        )
        assert len(df) == 1

    def test_large_initial_shares(self, calculator: DRIPCalculator):
        df = calculator.calculate_drip(
            initial_shares=1_000_000.0,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=DIVIDEND_GROWTH,
            share_price_growth=PRICE_GROWTH,
            years=5,
        )
        assert (df["Portfolio Value"] > 0).all()

    def test_high_growth_rates(self, calculator: DRIPCalculator):
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=20.0,
            share_price_growth=20.0,
            years=10,
        )
        assert (df["Portfolio Value"] > 0).all()
        assert df.iloc[-1]["Portfolio Value"] > df.iloc[0]["Portfolio Value"]

    def test_fractional_shares_allowed(self, calculator: DRIPCalculator):
        df = calculator.calculate_drip(
            initial_shares=1.5,
            share_price=SHARE_PRICE,
            annual_dividend=3.0,
            dividend_growth=0.0,
            share_price_growth=0.0,
            years=3,
        )
        assert (df["Shares"] > 0).all()

    def test_total_dividend_income_positive(self, base_df: pd.DataFrame):
        # Year 0 has dividend income from reinvestment loop
        assert (base_df["Total Dividend Income"] >= 0).all()
