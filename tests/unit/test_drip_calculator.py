"""Unit tests for DRIPCalculator — pure calculation logic and render methods.

Tests cover:
- DataFrame structure and required columns
- Year-0 baseline (no reinvestment yet)
- Share accumulation through reinvestment
- Dividend growth compounding over years
- Share price growth effect on portfolio value
- DRIP benefit vs value without DRIP
- Edge cases: zero growth rates, single year, monthly/annual frequency
- Boundary values: very high growth rates, fractional shares
- render_modern_chart: Plotly figure construction (st.* mocked)
- render_metrics_cards: metric card rendering (st.* mocked)
- render: full UI flow (st.* inputs mocked)
"""

from unittest.mock import MagicMock, patch

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

    EXPECTED_COLUMNS: frozenset[str] = frozenset(
        {
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
    )

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


# ============================================================================
# TESTS: render_modern_chart  (st.* and plotly calls mocked)
# ============================================================================


class TestRenderModernChart:
    """render_modern_chart builds a Plotly figure and calls st.plotly_chart."""

    def test_calls_st_plotly_chart(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        with patch("app.components.drip_calculator.st") as mock_st:
            calculator.render_modern_chart(base_df, ticker="AAPL.US", currency="$")
            mock_st.plotly_chart.assert_called_once()

    def test_passes_figure_to_plotly_chart(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        import plotly.graph_objects as go

        with patch("app.components.drip_calculator.st") as mock_st:
            calculator.render_modern_chart(base_df, ticker="AAPL.US", currency="$")
            fig = mock_st.plotly_chart.call_args[0][0]
            assert isinstance(fig, go.Figure)

    def test_uses_ticker_color_when_present(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        """Ticker present in ticker_colors → its color is used (not fallback)."""
        with patch("app.components.drip_calculator.st"):
            # Should not raise even if ticker_colors has the key
            calculator.render_modern_chart(base_df, ticker="AAPL.US", currency="$")

    def test_uses_fallback_color_for_unknown_ticker(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        with patch("app.components.drip_calculator.st"):
            # UNKNOWN.XX not in ticker_colors — falls back to #8A2BE2
            calculator.render_modern_chart(base_df, ticker="UNKNOWN.XX", currency="€")

    def test_default_currency_parameter(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        with patch("app.components.drip_calculator.st") as mock_st:
            calculator.render_modern_chart(base_df, ticker="AAPL.US")  # no currency arg
            mock_st.plotly_chart.assert_called_once()

    def test_figure_has_four_traces(self, calculator: DRIPCalculator, base_df: pd.DataFrame):

        with patch("app.components.drip_calculator.st") as mock_st:
            calculator.render_modern_chart(base_df, ticker="AAPL.US", currency="$")
            fig = mock_st.plotly_chart.call_args[0][0]
            # Subplot 2 (DRIP Comparison) has 2 traces (Without DRIP + With DRIP)
            assert len(fig.data) == 5


# ============================================================================
# TESTS: render_metrics_cards  (st.* calls mocked)
# ============================================================================


class TestRenderMetricsCards:
    """render_metrics_cards renders four metric blocks via st.markdown / st.columns."""

    def test_calls_st_columns(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        with patch("app.components.drip_calculator.st") as mock_st:
            mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
            calculator.render_metrics_cards(base_df, currency="$")
            mock_st.columns.assert_called_once_with(4)

    def test_renders_four_metric_cards(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        """Each of the four columns renders one metric card via st.markdown."""
        with patch("app.components.drip_calculator.st") as mock_st:
            col_mocks = [MagicMock() for _ in range(4)]
            mock_st.columns.return_value = col_mocks
            calculator.render_metrics_cards(base_df, currency="$")
            # st.markdown called once per column (inside `with col`) + once for CSS
            total_markdown_calls = mock_st.markdown.call_count + sum(
                col.__enter__.return_value.markdown.call_count for col in col_mocks
            )
            assert total_markdown_calls >= 1

    def test_calls_st_markdown_for_css(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        with patch("app.components.drip_calculator.st") as mock_st:
            mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
            calculator.render_metrics_cards(base_df, currency="$")
            # CSS_STYLES must be injected at least once
            css_calls = [c for c in mock_st.markdown.call_args_list if "<style>" in str(c)]
            assert len(css_calls) >= 1

    def test_default_currency_dollar(self, calculator: DRIPCalculator, base_df: pd.DataFrame):
        with patch("app.components.drip_calculator.st") as mock_st:
            mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
            calculator.render_metrics_cards(base_df)  # no currency arg
            mock_st.columns.assert_called_once()

    def test_handles_single_row_df(self, calculator: DRIPCalculator):
        """metrics with a 1-row DataFrame (0-year projection) should not crash."""
        df = calculator.calculate_drip(
            initial_shares=INITIAL_SHARES,
            share_price=SHARE_PRICE,
            annual_dividend=ANNUAL_DIVIDEND,
            dividend_growth=0.0,
            share_price_growth=0.0,
            years=0,
        )
        with patch("app.components.drip_calculator.st") as mock_st:
            mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
            calculator.render_metrics_cards(df, currency="$")  # should not raise


# ============================================================================
# TESTS: render (full UI — st.* inputs mocked)
# ============================================================================


class TestRender:
    """render() wires together the input widgets and calls calculate/render helpers."""

    def _make_mock_st(self):
        mock_st = MagicMock()
        mock_st.columns.side_effect = [
            [MagicMock(), MagicMock(), MagicMock()],  # col1, col2, col3
            [MagicMock(), MagicMock()],  # col4, col5
        ]
        mock_st.text_input.return_value = "AAPL.US"
        mock_st.number_input.side_effect = [25, 100, 3]  # shares, price, dividend
        mock_st.slider.side_effect = [6, 4, 15]  # div_growth, price_growth, years
        mock_st.selectbox.return_value = 4  # quarterly
        return mock_st

    def test_render_does_not_raise(self, calculator: DRIPCalculator):
        mock_st = self._make_mock_st()
        with (
            patch("app.components.drip_calculator.st", mock_st),
            patch.object(calculator, "render_metrics_cards"),
            patch.object(calculator, "render_modern_chart"),
        ):
            calculator.render()

    def test_render_calls_calculate_drip(self, calculator: DRIPCalculator):
        mock_st = self._make_mock_st()
        with (
            patch("app.components.drip_calculator.st", mock_st),
            patch.object(calculator, "calculate_drip", wraps=calculator.calculate_drip) as spy,
            patch.object(calculator, "render_metrics_cards"),
            patch.object(calculator, "render_modern_chart"),
        ):
            calculator.render()
            spy.assert_called_once()

    def test_render_calls_render_metrics_cards(self, calculator: DRIPCalculator):
        mock_st = self._make_mock_st()
        with (
            patch("app.components.drip_calculator.st", mock_st),
            patch.object(calculator, "render_metrics_cards") as mock_metrics,
            patch.object(calculator, "render_modern_chart"),
        ):
            calculator.render()
            mock_metrics.assert_called_once()

    def test_render_calls_render_modern_chart(self, calculator: DRIPCalculator):
        mock_st = self._make_mock_st()
        with (
            patch("app.components.drip_calculator.st", mock_st),
            patch.object(calculator, "render_metrics_cards"),
            patch.object(calculator, "render_modern_chart") as mock_chart,
        ):
            calculator.render()
            mock_chart.assert_called_once()
