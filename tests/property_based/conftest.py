"""Shared Hypothesis strategies for property-based tests.

These composite strategies encode domain constraints once and are reused
across all test modules in this package.
"""

from hypothesis import strategies as st


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
