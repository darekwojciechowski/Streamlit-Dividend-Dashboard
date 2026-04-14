"""Performance benchmarks for module-level colour utility functions."""

from __future__ import annotations

import pytest
from app.utils.color_manager import (
    adjust_gradient,
    apply_wcag_ui_standards,
    determine_text_color_for_dropdown,
    hex_to_rgba,
    rgb_to_hex,
)

from .conftest import _SAMPLE_HEX_COLORS, _SAMPLE_RGB_COLORS


@pytest.mark.benchmark
class TestColorUtilsPerformance:
    """Benchmarks for module-level colour helper functions in color_manager.

    These helpers are called on every render cycle for each ticker, so
    even small per-call overhead is multiplied by portfolio size.
    """

    # -----------------------------------------------------------------------
    # hex_to_rgba
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize("hex_color", _SAMPLE_HEX_COLORS)
    def test_hex_to_rgba_conversion(self, benchmark: pytest.fixture, hex_color: str) -> None:
        """Benchmark: hex → rgba conversion for all sample colours.

        Args:
            benchmark: pytest-benchmark fixture.
            hex_color: Input hex colour string.
        """
        result = benchmark(hex_to_rgba, hex_color, 0.8)
        assert result.startswith("rgba(")

    def test_hex_to_rgba_batch_200(self, benchmark: pytest.fixture) -> None:
        """Benchmark: converting 200 hex colours in one call batch.

        Args:
            benchmark: pytest-benchmark fixture.
        """

        def _batch() -> list[str]:
            return [hex_to_rgba(_SAMPLE_HEX_COLORS[i % len(_SAMPLE_HEX_COLORS)], 0.5) for i in range(200)]

        results = benchmark(_batch)
        assert len(results) == 200

    # -----------------------------------------------------------------------
    # rgb_to_hex
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize("rgb_color", _SAMPLE_RGB_COLORS)
    def test_rgb_to_hex_conversion(self, benchmark: pytest.fixture, rgb_color: str) -> None:
        """Benchmark: rgb → hex conversion for all sample colours.

        Args:
            benchmark: pytest-benchmark fixture.
            rgb_color: Input rgb() formatted colour string.
        """
        result = benchmark(rgb_to_hex, rgb_color)
        assert result.startswith("#")
        assert len(result) == 7

    # -----------------------------------------------------------------------
    # adjust_gradient
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "color",
        ["#FF6B6B", "#000000", "#FFFFFF", "rgb(78, 205, 196)"],
        ids=["pastel-red", "black", "white", "rgb-string"],
    )
    def test_adjust_gradient(self, benchmark: pytest.fixture, color: str) -> None:
        """Benchmark: gradient lightening for various input formats.

        Args:
            benchmark: pytest-benchmark fixture.
            color: Input colour in hex or rgb format.
        """
        result = benchmark(adjust_gradient, color)
        assert result.startswith("rgb(")

    # -----------------------------------------------------------------------
    # apply_wcag_ui_standards
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("color", "expected_light"),
        [
            ("#FFFFFF", True),
            ("#000000", False),
            ("#8A2BE2", False),
            ("#FFFF00", True),
        ],
        ids=["white", "black", "purple", "yellow"],
    )
    def test_wcag_luminance(
        self,
        benchmark: pytest.fixture,
        color: str,
        expected_light: bool,
    ) -> None:
        """Benchmark: WCAG luminance calculation is fast and correct.

        Args:
            benchmark: pytest-benchmark fixture.
            color: Input hex colour.
            expected_light: Expected return value of ``apply_wcag_ui_standards``.
        """
        result = benchmark(apply_wcag_ui_standards, color)
        assert result == expected_light

    # -----------------------------------------------------------------------
    # determine_text_color_for_dropdown
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("bg_color", "expected_text"),
        [
            ("#FFFFFF", "#000000"),
            ("#000000", "#FFFFFF"),
            ("#8A2BE2", "#FFFFFF"),
        ],
        ids=["light-bg", "dark-bg", "purple-bg"],
    )
    def test_determine_text_color(
        self,
        benchmark: pytest.fixture,
        bg_color: str,
        expected_text: str,
    ) -> None:
        """Benchmark: text colour selection returns a valid CSS colour string.

        Args:
            benchmark: pytest-benchmark fixture.
            bg_color: Background hex colour.
            expected_text: Expected ``"#000000"`` or ``"#FFFFFF"`` text colour.
        """
        result = benchmark(determine_text_color_for_dropdown, bg_color)
        assert result == expected_text
