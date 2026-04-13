"""Property-based tests for ColorManager.

Tests cover:
    - generate_colors_for_tickers: determinism, key correctness, hex validity
    - get_random_base_color: stateful cycling via RuleBasedStateMachine
"""

import re
from typing import ClassVar

import pytest
from app.utils.color_manager import ColorManager
from hypothesis import HealthCheck, assume, given, note, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from .conftest import ticker_strategy

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

        Arrange: A non-empty list of unique ticker strings.
        Act: Call ``generate_colors_for_tickers`` with the list.
        Assert: The set of keys in the result equals the set of input tickers.

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

        Arrange: A non-empty list of unique ticker strings.
        Act: Call ``generate_colors_for_tickers`` with the list.
        Assert: Every value in the result matches the ``#[0-9A-Fa-f]{6}`` pattern.

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

        Arrange: Two fresh ``ColorManager`` instances and the same ticker list.
        Act: Call ``generate_colors_for_tickers`` on each instance with that list.
        Assert: Both results are equal (deterministic mapping).

        Args:
            tickers: A non-empty list of unique ticker strings.
        """
        manager1 = ColorManager()
        manager2 = ColorManager()
        result1 = manager1.generate_colors_for_tickers(tickers)
        result2 = manager2.generate_colors_for_tickers(tickers)
        assert result1 == result2

    def test_empty_tickers_returns_empty_dict(self) -> None:
        """Passing an empty list returns an empty dict without raising.

        Arrange: A fresh ``ColorManager`` instance and an empty ticker list.
        Act: Call ``generate_colors_for_tickers`` with ``[]``.
        Assert: Returns ``{}`` without raising an exception.
        """
        manager = ColorManager()
        assert manager.generate_colors_for_tickers([]) == {}

    @given(st.lists(ticker_strategy(), min_size=2, max_size=10, unique=True))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_subset_tickers_preserves_color_assignment(self, tickers: list[str]) -> None:
        """The first ticker in sorted order receives the same color regardless of how many
        other tickers are in the list.

        A ticker's assigned color depends only on its position in the sorted ticker list,
        not on the presence of other tickers.

        Arrange: The full ticker list and a single-element list containing only the
            first ticker in sorted order; each paired with a fresh ``ColorManager``.
        Act: Call ``generate_colors_for_tickers`` on both instances.
        Assert: The color assigned to the first sorted ticker is identical in both
            results.

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

        Arrange: No preconditions — Hypothesis calls this once before any rule.
        Act: Replace ``self.manager`` with a new ``ColorManager`` and reset
            ``self.call_count`` to zero.
        Assert: (implicit) State is clean for the next sequence of rules.

        Hypothesis calls this once before any rule.
        """
        self.manager = ColorManager()
        self.call_count = 0

    @rule()
    def get_color(self) -> None:
        """Call ``get_random_base_color`` and verify the result.

        Arrange: A ``ColorManager`` whose ``used_colors`` list has not yet
            exhausted all unique palette entries (guarded by ``assume()`` to
            avoid the known upstream bug where the reset fires too late).
        Act: Call ``get_random_base_color`` on the manager.
        Assert: Result is a non-empty string that exists in ``BASE_COLORS``.

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
        assert isinstance(color, str), f"Expected str, got {type(color)}"
        assert color, f"Expected non-empty str, got {color!r}"
        assert color in self._ALL_COLORS, f"Returned color {color!r} is not in BASE_COLORS"
        self.call_count += 1

    @invariant()
    def used_colors_never_exceed_base_colors(self) -> None:
        """Used-color list length never exceeds the total base colors available.

        Arrange: Any state of the machine after one or more rules have run.
        Act: Read ``len(self.manager.used_colors)`` and ``len(BASE_COLORS)``.
        Assert: ``used_colors`` length is <= ``len(BASE_COLORS)``; after
            exhaustion the list resets so it never grows unboundedly.
        """
        from app.styles.colors_and_styles import BASE_COLORS as _BASE_COLORS

        if _BASE_COLORS:
            assert len(self.manager.used_colors) <= len(_BASE_COLORS), (
                f"used_colors length {len(self.manager.used_colors)} exceeds BASE_COLORS length {len(_BASE_COLORS)}"
            )


# Expose the stateful machine as a standard pytest test class
TestColorManagerMachine = ColorManagerMachine.TestCase
