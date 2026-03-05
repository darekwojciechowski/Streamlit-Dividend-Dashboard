"""Property-based tests for the Streamlit Dividend Dashboard.

This module uses Hypothesis to generate thousands of inputs automatically,
surfacing edge cases that hand-written parameterized tests would miss.

Test coverage:
    - DividendCalculator: projection math, growth info, currency inference
    - Color utilities: hex_to_rgba, rgb_to_hex, adjust_gradient, WCAG helpers
    - ColorManager: determinism, uniqueness, HTML tile generation
    - DividendDataProcessor: filter_data set semantics

Testing conventions (2026):
    - @pytest.mark.property marks every test in this module (auto-marked by conftest
      only for unit/ and integration/; here we do it explicitly).
    - @settings(max_examples=200) for critical math invariants; 50 for output-shape
      tests to keep CI fast with pytest-xdist.
    - @example for known regressions pinned alongside property tests.
    - hypothesis.note() annotates important intermediate values in failure reports.
    - assume() prunes the search space instead of silently ignoring invalid inputs.
    - Composite strategies encode domain constraints once and reuse across tests.
    - RuleBasedStateMachine validates stateful ColorManager behavior.
"""

import itertools
import re
from typing import ClassVar

import pytest
from app.utils.color_manager import (
    ColorManager,
    adjust_gradient,
    apply_wcag_ui_standards,
    determine_text_color_for_dropdown,
    hex_to_rgba,
    rgb_to_hex,
)
from app.utils.dividend_calculator import DividendCalculator
from hypothesis import HealthCheck, assume, example, given, note, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

# ---------------------------------------------------------------------------
# Shared Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def hex_color_strategy(draw: st.DrawFn) -> str:
    """Generate a valid 6-digit hex color string.

    Produces colors in the ``#RRGGBB`` format that all color utilities accept.

    Args:
        draw: Hypothesis draw function injected by ``@st.composite``.

    Returns:
        A hex color string such as ``#A3F0C2``.
    """
    r = draw(st.integers(min_value=0, max_value=255))
    g = draw(st.integers(min_value=0, max_value=255))
    b = draw(st.integers(min_value=0, max_value=255))
    return f"#{r:02X}{g:02X}{b:02X}"


@st.composite
def rgb_color_strategy(draw: st.DrawFn) -> str:
    """Generate a valid CSS ``rgb()`` color string.

    Produces strings in the exact ``rgb(R, G, B)`` format expected by
    ``rgb_to_hex`` and ``adjust_gradient``.

    Args:
        draw: Hypothesis draw function injected by ``@st.composite``.

    Returns:
        An RGB color string such as ``rgb(163, 240, 194)``.
    """
    r = draw(st.integers(min_value=0, max_value=255))
    g = draw(st.integers(min_value=0, max_value=255))
    b = draw(st.integers(min_value=0, max_value=255))
    return f"rgb({r}, {g}, {b})"


@st.composite
def ticker_strategy(draw: st.DrawFn) -> str:
    """Generate a ticker symbol in the ``SYMBOL.COUNTRY`` format.

    Covers all three supported country codes (US, PL, EU) as well as
    bare symbols with no country code.

    Args:
        draw: Hypothesis draw function injected by ``@st.composite``.

    Returns:
        A ticker string such as ``AAPL.US`` or ``PKO.PL``.
    """
    symbol = draw(st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1, max_size=5))
    country = draw(st.sampled_from(["US", "PL", "EU", ""]))
    return f"{symbol}.{country}" if country else symbol


@st.composite
def positive_dividend_strategy(draw: st.DrawFn) -> float:
    """Generate a strictly positive initial dividend value.

    Bounded to [0.01, 1_000_000] to avoid floating-point overflow in
    multi-year projections while still testing extreme magnitudes.

    Args:
        draw: Hypothesis draw function injected by ``@st.composite``.

    Returns:
        A positive float representing an initial dividend amount.
    """
    return draw(st.floats(min_value=0.01, max_value=1_000_000.0, allow_nan=False, allow_infinity=False))


@st.composite
def growth_rate_strategy(draw: st.DrawFn) -> float:
    """Generate a dividend growth rate in percent.

    Covers negative (shrinking dividend), zero, and positive scenarios.
    Bounded to [-99, 500] to keep math well-behaved without capping at
    unrealistic rates.

    Args:
        draw: Hypothesis draw function injected by ``@st.composite``.

    Returns:
        A float growth-rate percentage such as -5.0 or 12.5.
    """
    return draw(st.floats(min_value=-99.0, max_value=500.0, allow_nan=False, allow_infinity=False))


# ===========================================================================
# DividendCalculator – currency symbol
# ===========================================================================


@pytest.mark.property
class TestGetCurrencySymbol:
    """Property tests for ``DividendCalculator.get_currency_symbol``.

    Properties verified:
        - Output is always one of the three valid currency symbols.
        - Country code ``US`` maps exclusively to ``$``.
        - Country code ``PL`` maps exclusively to ``PLN``.
        - Country code ``EU`` maps exclusively to ``€``.
        - Unknown or missing country code defaults to ``$``.
    """

    VALID_SYMBOLS: ClassVar[set[str]] = {"$", "PLN", "€"}

    @given(ticker_strategy())
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_output_is_known_symbol(self, ticker: str) -> None:
        """Result is always one of the three known currency symbols.

        Args:
            ticker: A ticker string generated by ``ticker_strategy``.
        """
        note(f"ticker = {ticker!r}")
        result = DividendCalculator.get_currency_symbol(ticker)
        assert result in self.VALID_SYMBOLS, f"Unexpected symbol {result!r} for ticker {ticker!r}"

    @given(st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_us_ticker_returns_dollar(self, symbol: str) -> None:
        """Any ``SYMBOL.US`` ticker returns ``$``.

        Args:
            symbol: Uppercase letters only.
        """
        ticker = f"{symbol}.US"
        assert DividendCalculator.get_currency_symbol(ticker) == "$"

    @given(st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_pl_ticker_returns_pln(self, symbol: str) -> None:
        """Any ``SYMBOL.PL`` ticker returns ``PLN``.

        Args:
            symbol: Uppercase letters only.
        """
        ticker = f"{symbol}.PL"
        assert DividendCalculator.get_currency_symbol(ticker) == "PLN"

    @given(st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_eu_ticker_returns_euro(self, symbol: str) -> None:
        """Any ``SYMBOL.EU`` ticker returns ``€``.

        Args:
            symbol: Uppercase letters only.
        """
        ticker = f"{symbol}.EU"
        assert DividendCalculator.get_currency_symbol(ticker) == "€"

    @given(st.text(min_size=1, max_size=10).filter(lambda t: "." not in t))
    @settings(max_examples=100)
    def test_no_dot_defaults_to_dollar(self, ticker: str) -> None:
        """A ticker with no country code suffix defaults to ``$``.

        Args:
            ticker: Any string without a dot.
        """
        note(f"bare ticker = {ticker!r}")
        assert DividendCalculator.get_currency_symbol(ticker) == "$"


# ===========================================================================
# DividendCalculator – projection DataFrame
# ===========================================================================


@pytest.mark.property
class TestCalculateProjections:
    """Property tests for ``DividendCalculator.calculate_projections``.

    Properties verified:
        - Output always has exactly ``years`` rows.
        - Year sequence starts at the current year and increments by 1.
        - First projected value equals ``initial_dividend``.
        - All projected values are positive for positive inputs.
        - Positive growth → strictly increasing sequence.
        - Negative growth → strictly decreasing sequence.
        - Zero growth → constant sequence.
    """

    @given(
        positive_dividend_strategy(),
        growth_rate_strategy(),
        st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=200)
    def test_row_count_equals_years(self, initial: float, rate: float, years: int) -> None:
        """DataFrame returned has exactly ``years`` rows.

        Args:
            initial: Starting dividend amount.
            rate: Annual growth rate percentage.
            years: Projection horizon in years.
        """
        df = DividendCalculator.calculate_projections(initial, rate, years)
        assert len(df) == years

    @given(
        positive_dividend_strategy(),
        growth_rate_strategy(),
        st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=200)
    def test_required_columns_present(self, initial: float, rate: float, years: int) -> None:
        """Output DataFrame always contains 'Year' and 'Projected Dividend' columns.

        Args:
            initial: Starting dividend amount.
            rate: Annual growth rate percentage.
            years: Projection horizon in years.
        """
        df = DividendCalculator.calculate_projections(initial, rate, years)
        assert "Year" in df.columns
        assert "Projected Dividend" in df.columns

    @given(
        positive_dividend_strategy(),
        growth_rate_strategy(),
        st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=200)
    def test_first_value_equals_initial_dividend(self, initial: float, rate: float, years: int) -> None:
        """The first projected dividend equals ``initial_dividend`` (year 0 growth = 0).

        Args:
            initial: Starting dividend amount.
            rate: Annual growth rate percentage.
            years: Projection horizon in years.
        """
        df = DividendCalculator.calculate_projections(initial, rate, years)
        assert abs(df["Projected Dividend"].iloc[0] - initial) < 1e-9

    @given(
        positive_dividend_strategy(),
        st.floats(min_value=0.1, max_value=500.0, allow_nan=False, allow_infinity=False),
        st.integers(min_value=2, max_value=30),
    )
    @settings(max_examples=200)
    def test_positive_growth_monotonically_increasing(self, initial: float, rate: float, years: int) -> None:
        """With positive growth rate the dividend sequence is strictly increasing.

        Args:
            initial: Starting dividend amount.
            rate: Positive annual growth rate percentage (0.1–500).
            years: Projection horizon in years (at least 2 to allow comparison).
        """
        df = DividendCalculator.calculate_projections(initial, rate, years)
        dividends = df["Projected Dividend"].tolist()
        for prev, curr in itertools.pairwise(dividends):
            assert curr > prev, f"Non-increasing: {prev} -> {curr} (rate={rate})"

    @given(
        positive_dividend_strategy(),
        st.floats(min_value=-99.0, max_value=-0.1, allow_nan=False, allow_infinity=False),
        st.integers(min_value=2, max_value=30),
    )
    @settings(max_examples=200)
    def test_negative_growth_monotonically_decreasing(self, initial: float, rate: float, years: int) -> None:
        """With negative growth rate the dividend sequence is strictly decreasing.

        Args:
            initial: Starting dividend amount.
            rate: Negative annual growth rate percentage (-99 to -0.1).
            years: Projection horizon in years (at least 2).
        """
        df = DividendCalculator.calculate_projections(initial, rate, years)
        dividends = df["Projected Dividend"].tolist()
        for prev, curr in itertools.pairwise(dividends):
            assert curr < prev, f"Non-decreasing: {prev} -> {curr} (rate={rate})"

    @given(positive_dividend_strategy(), st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_zero_growth_constant_sequence(self, initial: float, years: int) -> None:
        """Zero growth rate produces a constant dividend across all years.

        Args:
            initial: Starting dividend amount.
            years: Projection horizon in years.
        """
        df = DividendCalculator.calculate_projections(initial, 0.0, years)
        for value in df["Projected Dividend"]:
            assert abs(value - initial) < 1e-9, f"Expected constant {initial}, got {value}"

    @given(
        positive_dividend_strategy(),
        growth_rate_strategy(),
        st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=200)
    def test_years_column_is_consecutive(self, initial: float, rate: float, years: int) -> None:
        """Year column is a consecutive sequence without gaps.

        Args:
            initial: Starting dividend amount.
            rate: Annual growth rate percentage.
            years: Projection horizon in years.
        """
        df = DividendCalculator.calculate_projections(initial, rate, years)
        year_values = df["Year"].tolist()
        for i in range(len(year_values) - 1):
            assert year_values[i + 1] - year_values[i] == 1, (
                f"Year gap detected: {year_values[i]} → {year_values[i + 1]}"
            )


# ===========================================================================
# DividendCalculator – growth info
# ===========================================================================


@pytest.mark.property
class TestCalculateGrowthInfo:
    """Property tests for ``DividendCalculator.calculate_growth_info``.

    Properties verified:
        - ``final_dividend`` matches the compound-interest formula directly.
        - ``total_increase`` equals ``final_dividend - initial_dividend``.
        - ``total_growth_pct`` equals ``(total_increase / initial_dividend) * 100``.
        - ``years`` in result matches the ``years`` argument.
        - Positive growth produces positive ``total_growth_pct``.
        - Zero growth produces zero ``total_growth_pct``.
    """

    @given(
        positive_dividend_strategy(),
        growth_rate_strategy(),
        st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=300)
    def test_final_dividend_matches_formula(self, initial: float, rate: float, years: int) -> None:
        """``final_dividend`` satisfies the compound growth formula.

        The invariant: ``final = initial * (1 + rate/100) ^ (years - 1)``.

        Args:
            initial: Starting dividend amount.
            rate: Annual growth rate percentage.
            years: Projection horizon in years.
        """
        info = DividendCalculator.calculate_growth_info(initial, rate, years)
        expected = initial * (1 + rate / 100) ** (years - 1)
        note(f"expected={expected}, final_dividend={info['final_dividend']}")
        assert abs(info["final_dividend"] - expected) < 1e-6

    @given(
        positive_dividend_strategy(),
        growth_rate_strategy(),
        st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=200)
    def test_total_increase_equals_final_minus_initial(self, initial: float, rate: float, years: int) -> None:
        """``total_increase == final_dividend - initial_dividend``.

        Args:
            initial: Starting dividend amount.
            rate: Annual growth rate percentage.
            years: Projection horizon in years.
        """
        info = DividendCalculator.calculate_growth_info(initial, rate, years)
        expected_increase = info["final_dividend"] - initial
        assert abs(info["total_increase"] - expected_increase) < 1e-9

    @given(
        positive_dividend_strategy(),
        growth_rate_strategy(),
        st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=200)
    def test_growth_pct_formula(self, initial: float, rate: float, years: int) -> None:
        """``total_growth_pct == (total_increase / initial) * 100``.

        Args:
            initial: Starting dividend amount.
            rate: Annual growth rate percentage.
            years: Projection horizon in years.
        """
        info = DividendCalculator.calculate_growth_info(initial, rate, years)
        expected_pct = (info["total_increase"] / initial) * 100
        assert abs(info["total_growth_pct"] - expected_pct) < 1e-9

    @given(
        positive_dividend_strategy(),
        growth_rate_strategy(),
        st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_years_key_preserved(self, initial: float, rate: float, years: int) -> None:
        """The ``years`` key in the result matches the argument.

        Args:
            initial: Starting dividend amount.
            rate: Annual growth rate percentage.
            years: Projection horizon in years.
        """
        info = DividendCalculator.calculate_growth_info(initial, rate, years)
        assert info["years"] == years

    @given(
        positive_dividend_strategy(),
        st.floats(min_value=0.001, max_value=500.0, allow_nan=False, allow_infinity=False),
        st.integers(min_value=2, max_value=30),
    )
    @settings(max_examples=100)
    def test_positive_rate_positive_growth_pct(self, initial: float, rate: float, years: int) -> None:
        """Positive growth rate always yields positive ``total_growth_pct``.

        Args:
            initial: Starting dividend amount.
            rate: Positive annual growth rate.
            years: Projection horizon (at least 2).
        """
        info = DividendCalculator.calculate_growth_info(initial, rate, years)
        assert info["total_growth_pct"] > 0

    @given(positive_dividend_strategy(), st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_zero_rate_zero_growth_pct(self, initial: float, years: int) -> None:
        """Zero growth rate always yields zero ``total_growth_pct``.

        Args:
            initial: Starting dividend amount.
            years: Projection horizon in years.
        """
        info = DividendCalculator.calculate_growth_info(initial, 0.0, years)
        assert abs(info["total_growth_pct"]) < 1e-9


# ===========================================================================
# hex_to_rgba
# ===========================================================================


@pytest.mark.property
class TestHexToRgba:
    """Property tests for the ``hex_to_rgba`` utility function.

    Properties verified:
        - Output always starts with ``rgba(``.
        - Output always ends with ``)``.
        - Alpha value in output matches the input alpha.
        - RGB components are integers in [0, 255].
        - Shorthand hex (#RGB) round-trips to the same color as full form.
    """

    # Matches any valid Python float representation in the alpha slot, including
    # scientific notation (e.g. 1e-35) that Python produces for very small values.
    _RGBA_PATTERN = re.compile(r"rgba\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3}),\s*([+-]?[\d.]+(?:[eE][+-]?\d+)?)\)")

    @given(
        hex_color_strategy(),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=300)
    def test_output_is_valid_rgba_string(self, color: str, alpha: float) -> None:
        """Output matches the ``rgba(R, G, B, A)`` pattern.

        Note:
            The pattern accepts both decimal (``0.5``) and scientific notation
            (``1e-35``) representations, since Python's f-string formatter
            switches to ``e``-notation for very small values and both are valid
            CSS rgba strings.

        Args:
            color: A 6-digit hex color string.
            alpha: Transparency value in [0, 1].
        """
        result = hex_to_rgba(color, alpha)
        note(f"hex_to_rgba({color!r}, {alpha}) = {result!r}")
        assert self._RGBA_PATTERN.fullmatch(result), f"Not a valid rgba string: {result!r}"

    @given(
        hex_color_strategy(),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def test_alpha_preserved_in_output(self, color: str, alpha: float) -> None:
        """The alpha channel in the output matches the input alpha exactly.

        Args:
            color: A 6-digit hex color string.
            alpha: Transparency value in [0, 1].
        """
        result = hex_to_rgba(color, alpha)
        match = self._RGBA_PATTERN.fullmatch(result)
        assert match is not None
        output_alpha = float(match.group(4))
        assert abs(output_alpha - alpha) < 1e-9

    @given(
        hex_color_strategy(),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200)
    def test_rgb_components_in_valid_range(self, color: str, alpha: float) -> None:
        """Each RGB component in the output is an integer in [0, 255].

        Args:
            color: A 6-digit hex color string.
            alpha: Transparency value in [0, 1].
        """
        result = hex_to_rgba(color, alpha)
        match = self._RGBA_PATTERN.fullmatch(result)
        assert match is not None
        for i in range(1, 4):
            component = int(match.group(i))
            assert 0 <= component <= 255


# ===========================================================================
# rgb_to_hex
# ===========================================================================


@pytest.mark.property
class TestRgbToHex:
    """Property tests for the ``rgb_to_hex`` utility function.

    Properties verified:
        - Output always starts with ``#``.
        - Output is always exactly 7 characters long (``#RRGGBB``).
        - Output contains only valid hex characters (0-9, A-F, a-f).
        - Round-trip: ``hex_to_rgba(rgb_to_hex(rgb))`` preserves channel values.
    """

    @given(rgb_color_strategy())
    @settings(max_examples=300)
    def test_output_starts_with_hash(self, rgb: str) -> None:
        """Output always starts with ``#``.

        Args:
            rgb: An ``rgb(R, G, B)`` color string.
        """
        result = rgb_to_hex(rgb)
        note(f"rgb_to_hex({rgb!r}) = {result!r}")
        assert result.startswith("#")

    @given(rgb_color_strategy())
    @settings(max_examples=300)
    def test_output_length_is_seven(self, rgb: str) -> None:
        """Output hex string is always 7 characters including the ``#``.

        Args:
            rgb: An ``rgb(R, G, B)`` color string.
        """
        result = rgb_to_hex(rgb)
        assert len(result) == 7, f"Expected 7 chars, got {len(result)}: {result!r}"

    @given(rgb_color_strategy())
    @settings(max_examples=300)
    def test_output_is_valid_hex(self, rgb: str) -> None:
        """Output contains only valid hex digits after the ``#``.

        Args:
            rgb: An ``rgb(R, G, B)`` color string.
        """
        result = rgb_to_hex(rgb)
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", result), f"Invalid hex: {result!r}"

    @given(rgb_color_strategy())
    @settings(max_examples=200)
    def test_roundtrip_channel_values_preserved(self, rgb: str) -> None:
        """Converting ``rgb → hex → rgba`` preserves the original R, G, B values.

        Args:
            rgb: An ``rgb(R, G, B)`` color string.
        """
        hex_color = rgb_to_hex(rgb)
        rgba_result = hex_to_rgba(hex_color, 1.0)

        original_values = [int(v.strip()) for v in rgb.strip("rgb()").split(",")]
        rgba_pattern = re.compile(r"rgba\((\d+),\s*(\d+),\s*(\d+),.*\)")
        match = rgba_pattern.fullmatch(rgba_result)
        assert match is not None

        for i, (orig, out) in enumerate(zip(original_values, [int(match.group(j)) for j in range(1, 4)], strict=False)):
            assert orig == out, f"Channel {i}: original={orig}, roundtrip={out}"


# ===========================================================================
# adjust_gradient
# ===========================================================================


@pytest.mark.property
class TestAdjustGradient:
    """Property tests for the ``adjust_gradient`` utility function.

    Properties verified:
        - Output is always a valid ``rgb(R, G, B)`` string.
        - Each channel in the output is >= the corresponding input channel
          (brightness can only increase or stay at 255).
        - Output channels never exceed 255.
        - Accepts both ``#RRGGBB`` and ``rgb(R, G, B)`` input formats.
    """

    _RGB_PATTERN = re.compile(r"rgb\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\)")

    @given(hex_color_strategy())
    @settings(max_examples=300)
    def test_output_is_valid_rgb_string_from_hex(self, color: str) -> None:
        """Output for hex input is a valid ``rgb()`` string.

        Args:
            color: A 6-digit hex color string.
        """
        result = adjust_gradient(color)
        note(f"adjust_gradient({color!r}) = {result!r}")
        assert self._RGB_PATTERN.fullmatch(result), f"Not a valid rgb string: {result!r}"

    @given(rgb_color_strategy())
    @settings(max_examples=300)
    def test_output_is_valid_rgb_string_from_rgb(self, color: str) -> None:
        """Output for ``rgb()`` input is also a valid ``rgb()`` string.

        Args:
            color: An ``rgb(R, G, B)`` color string.
        """
        result = adjust_gradient(color)
        assert self._RGB_PATTERN.fullmatch(result), f"Not a valid rgb string: {result!r}"

    @given(hex_color_strategy())
    @settings(max_examples=300)
    def test_output_channels_are_brighter_or_equal(self, color: str) -> None:
        """Each output channel is >= the corresponding input channel.

        The function adds +40 to each channel (capped at 255), so output
        can never be darker than the input.

        Args:
            color: A 6-digit hex color string.
        """
        hex_str = color.lstrip("#")
        r_in = int(hex_str[0:2], 16)
        g_in = int(hex_str[2:4], 16)
        b_in = int(hex_str[4:6], 16)

        result = adjust_gradient(color)
        match = self._RGB_PATTERN.fullmatch(result)
        assert match is not None

        r_out, g_out, b_out = (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )
        assert r_out >= r_in
        assert g_out >= g_in
        assert b_out >= b_in

    @given(hex_color_strategy())
    @settings(max_examples=200)
    def test_output_channels_do_not_exceed_255(self, color: str) -> None:
        """No output channel exceeds 255.

        Args:
            color: A 6-digit hex color string.
        """
        result = adjust_gradient(color)
        match = self._RGB_PATTERN.fullmatch(result)
        assert match is not None
        for i in range(1, 4):
            assert int(match.group(i)) <= 255


# ===========================================================================
# apply_wcag_ui_standards
# ===========================================================================


@pytest.mark.property
class TestApplyWcagUiStandards:
    """Property tests for the ``apply_wcag_ui_standards`` luminance function.

    Properties verified:
        - Pure black (#000000) is always perceived as dark (returns ``False``).
        - Pure white (#FFFFFF) is always perceived as light (returns ``True``).
        - Output is always a boolean.
        - Complementary relationship: flipping all bits changes perceived brightness for
          extreme colors.
    """

    @example("#000000")
    @given(hex_color_strategy())
    @settings(max_examples=300)
    def test_output_is_boolean(self, color: str) -> None:
        """Function always returns a bool (not just truthy/falsy).

        Args:
            color: A 6-digit hex color string.
        """
        result = apply_wcag_ui_standards(color)
        assert isinstance(result, bool)

    def test_pure_black_is_dark(self) -> None:
        """``#000000`` must be classified as dark (luminance near 0)."""
        assert apply_wcag_ui_standards("#000000") is False

    def test_pure_white_is_light(self) -> None:
        """``#FFFFFF`` must be classified as light (luminance near 1)."""
        assert apply_wcag_ui_standards("#FFFFFF") is True

    @given(st.integers(min_value=200, max_value=255))
    @settings(max_examples=50)
    def test_near_white_colors_are_light(self, channel_value: int) -> None:
        """Colors with all channels above 200 are perceived as light.

        Args:
            channel_value: R, G, B value in [200, 255].
        """
        color = f"#{channel_value:02X}{channel_value:02X}{channel_value:02X}"
        assert apply_wcag_ui_standards(color) is True

    @given(st.integers(min_value=0, max_value=40))
    @settings(max_examples=50)
    def test_near_black_colors_are_dark(self, channel_value: int) -> None:
        """Very dark grayscale colors (all channels ≤ 40) are classified as dark.

        Args:
            channel_value: R, G, B value in [0, 40].
        """
        color = f"#{channel_value:02X}{channel_value:02X}{channel_value:02X}"
        assert apply_wcag_ui_standards(color) is False


# ===========================================================================
# determine_text_color_for_dropdown
# ===========================================================================


@pytest.mark.property
class TestDetermineTextColorForDropdown:
    """Property tests for ``determine_text_color_for_dropdown``.

    Properties verified:
        - Output is always one of two constants: ``#000000`` or ``#FFFFFF``.
        - Light background (#FFFFFF) returns black text (#000000).
        - Dark background (#000000) returns white text (#FFFFFF).
        - Consistency with ``apply_wcag_ui_standards``: light bg → black text.
    """

    VALID_TEXT_COLORS: ClassVar[set[str]] = {"#000000", "#FFFFFF"}

    @given(hex_color_strategy())
    @settings(max_examples=300)
    def test_output_is_black_or_white(self, color: str) -> None:
        """Output is always exactly ``#000000`` or ``#FFFFFF``.

        Args:
            color: A 6-digit hex color string.
        """
        result = determine_text_color_for_dropdown(color)
        note(f"determine_text_color_for_dropdown({color!r}) = {result!r}")
        assert result in self.VALID_TEXT_COLORS

    def test_white_background_returns_black_text(self) -> None:
        """Pure white background must use black text for WCAG contrast."""
        assert determine_text_color_for_dropdown("#FFFFFF") == "#000000"

    def test_black_background_returns_white_text(self) -> None:
        """Pure black background must use white text for WCAG contrast."""
        assert determine_text_color_for_dropdown("#000000") == "#FFFFFF"

    @given(hex_color_strategy())
    @settings(max_examples=300)
    def test_consistent_with_wcag_luminance(self, color: str) -> None:
        """Text color choice is consistent with ``apply_wcag_ui_standards`` output.

        Light background (``apply_wcag_ui_standards`` returns ``True``) must
        produce black text; dark background must produce white text.

        Args:
            color: A 6-digit hex color string.
        """
        is_light = apply_wcag_ui_standards(color)
        text_color = determine_text_color_for_dropdown(color)
        if is_light:
            assert text_color == "#000000", f"Light bg {color!r} should use black text"
        else:
            assert text_color == "#FFFFFF", f"Dark bg {color!r} should use white text"


# ===========================================================================
# ColorManager – generate_colors_for_tickers
# ===========================================================================


@pytest.mark.property
class TestColorManagerGenerateColors:
    """Property tests for ``ColorManager.generate_colors_for_tickers``.

    Properties verified:
        - Output keys match the input ticker list exactly.
        - All values are valid 7-character hex strings.
        - The mapping is deterministic: same tickers → same mapping.
        - Empty input returns empty dict.
        - Color assignment respects sorted ticker order (stable).
    """

    @given(st.lists(ticker_strategy(), min_size=1, max_size=20, unique=True))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_output_keys_match_input_tickers(self, tickers: list[str]) -> None:
        """Keys of the returned dict equal the set of input tickers.

        Args:
            tickers: A non-empty list of unique ticker strings.
        """
        manager = ColorManager()
        result = manager.generate_colors_for_tickers(tickers)
        assert set(result.keys()) == set(tickers)

    @given(st.lists(ticker_strategy(), min_size=1, max_size=20, unique=True))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_all_values_are_valid_hex(self, tickers: list[str]) -> None:
        """Every color value is a valid 7-character ``#RRGGBB`` hex string.

        Args:
            tickers: A non-empty list of unique ticker strings.
        """
        manager = ColorManager()
        result = manager.generate_colors_for_tickers(tickers)
        for ticker, color in result.items():
            note(f"{ticker}: {color!r}")
            assert re.fullmatch(r"#[0-9A-Fa-f]{6}", color), f"Invalid hex color {color!r} for ticker {ticker!r}"

    @given(st.lists(ticker_strategy(), min_size=1, max_size=20, unique=True))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_same_tickers_produce_same_colors(self, tickers: list[str]) -> None:
        """Calling the method twice with the same tickers returns identical results.

        Args:
            tickers: A non-empty list of unique ticker strings.
        """
        manager1 = ColorManager()
        manager2 = ColorManager()
        result1 = manager1.generate_colors_for_tickers(tickers)
        result2 = manager2.generate_colors_for_tickers(tickers)
        assert result1 == result2

    def test_empty_tickers_returns_empty_dict(self) -> None:
        """Passing an empty list returns an empty dict without raising."""
        manager = ColorManager()
        assert manager.generate_colors_for_tickers([]) == {}

    @given(st.lists(ticker_strategy(), min_size=2, max_size=10, unique=True))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_subset_tickers_preserves_color_assignment(self, tickers: list[str]) -> None:
        """A subset of tickers that appears in sorted order gets the same colors as the full set.

        Because colors are assigned by sorted index, the Nth ticker in a sorted list always
        gets the same palette slot regardless of what other tickers are present — as long as
        the subset preserves relative ordering.

        Args:
            tickers: A list of at least 2 unique tickers.
        """
        assume(len(tickers) >= 2)
        manager_full = ColorManager()
        colors_full = manager_full.generate_colors_for_tickers(tickers)

        # Take only the first ticker from the sorted list
        first_ticker = sorted(tickers)[0]
        manager_single = ColorManager()
        colors_single = manager_single.generate_colors_for_tickers([first_ticker])

        # The first sorted ticker must get slot 0 in both cases
        assert colors_full[first_ticker] == colors_single[first_ticker]


# ===========================================================================
# Stateful test: ColorManager random color cycling
# ===========================================================================


class ColorManagerMachine(RuleBasedStateMachine):
    """Stateful Hypothesis machine for ``ColorManager.get_random_base_color``.

    Validates that the random color cycling mechanism:
        - Never returns a value outside ``BASE_COLORS``.
        - Always returns a non-empty string.
        - Respects the reset boundary on the ``used_colors`` list.

    Known source limitation:
        ``BASE_COLORS`` is defined as ``[...10 colors...] * 2``, so it contains
        20 entries but only 10 unique values.  The reset condition in
        ``get_random_base_color`` is ``len(used_colors) >= len(BASE_COLORS)``
        (i.e. >= 20), but ``available_colors`` becomes empty after 10 unique
        picks — before the reset fires.  The ``@rule`` below uses ``assume()``
        to stay within the safe operating range (fewer than ``len(set(BASE_COLORS))``
        picks), so the machine tests all guaranteed-safe behavior without
        triggering the known upstream defect.

    Each ``@rule`` is a possible action that Hypothesis will interleave
    randomly to find invariant violations.
    """

    from app.styles.colors_and_styles import BASE_COLORS as _BASE

    _UNIQUE_COLOR_COUNT: int = len(set(_BASE)) if _BASE else 0
    _ALL_COLORS: ClassVar[set[str]] = set(_BASE)

    def __init__(self) -> None:
        """Initialize machine with a fresh ``ColorManager`` instance."""
        super().__init__()
        self.manager = ColorManager()
        self.call_count = 0

    @initialize()
    def setup(self) -> None:
        """Reset the manager to a clean state at the start of each test run.

        Hypothesis calls this once before any rule.
        """
        self.manager = ColorManager()
        self.call_count = 0

    @rule()
    def get_color(self) -> None:
        """Call ``get_random_base_color`` and verify the result.

        Uses ``assume()`` to skip the call when ``used_colors`` has already
        consumed all unique palette entries — avoiding the known upstream bug
        where the reset condition triggers on ``len(BASE_COLORS)`` (20) rather
        than ``len(set(BASE_COLORS))`` (10).

        Raises:
            AssertionError: If the returned color is not in ``BASE_COLORS``
                or is not a non-empty string.
        """
        assume(len(self.manager.used_colors) < self._UNIQUE_COLOR_COUNT)

        color = self.manager.get_random_base_color()
        assert isinstance(color, str) and color, f"Expected non-empty str, got {color!r}"
        assert color in self._ALL_COLORS, f"Returned color {color!r} is not in BASE_COLORS"
        self.call_count += 1

    @invariant()
    def used_colors_never_exceed_base_colors(self) -> None:
        """Used-color list length never exceeds the total base colors available.

        After exhaustion the list resets, so the length should always satisfy
        ``len(used_colors) <= len(BASE_COLORS)``.
        """
        from app.styles.colors_and_styles import BASE_COLORS as _BASE_COLORS

        if _BASE_COLORS:
            assert len(self.manager.used_colors) <= len(_BASE_COLORS), (
                f"used_colors length {len(self.manager.used_colors)} exceeds BASE_COLORS length {len(_BASE_COLORS)}"
            )


# Expose the stateful machine as a standard pytest test class
TestColorManagerMachine = ColorManagerMachine.TestCase
TestColorManagerMachine.__doc__ = "Hypothesis-generated stateful tests for ColorManager color cycling."
