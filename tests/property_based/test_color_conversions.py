"""Property-based tests for color conversion utilities.

Tests cover:
    - hex_to_rgba: hex + alpha → CSS rgba() string
    - rgb_to_hex: CSS rgb() → hex string, including round-trip integrity
"""

import re

import pytest
from app.utils.color_manager import hex_to_rgba, rgb_to_hex
from hypothesis import given, note, settings
from hypothesis import strategies as st

from .conftest import hex_color_strategy, rgb_color_strategy

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

        Arrange: A 6-digit hex color string and an alpha value in [0, 1].
        Act: Call ``hex_to_rgba`` with those values.
        Assert: Output fully matches the ``rgba(R, G, B, A)`` pattern, accepting
            both decimal and scientific notation for the alpha component.

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

        Arrange: A 6-digit hex color string and an alpha value in [0, 1].
        Act: Call ``hex_to_rgba`` and extract the fourth component from the output.
        Assert: Extracted alpha equals the input alpha within floating-point tolerance.

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

        Arrange: A 6-digit hex color string and an alpha value in [0, 1].
        Act: Call ``hex_to_rgba`` and extract the R, G, B components from the output.
        Assert: Each component is an integer in the range [0, 255].

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

        Arrange: A valid ``rgb(R, G, B)`` color string.
        Act: Call ``rgb_to_hex`` with the string.
        Assert: The result starts with ``#``.

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

        Arrange: A valid ``rgb(R, G, B)`` color string.
        Act: Call ``rgb_to_hex`` with the string.
        Assert: The result is exactly 7 characters long.

        Args:
            rgb: An ``rgb(R, G, B)`` color string.
        """
        result = rgb_to_hex(rgb)
        assert len(result) == 7, f"Expected 7 chars, got {len(result)}: {result!r}"

    @given(rgb_color_strategy())
    @settings(max_examples=300)
    def test_output_is_valid_hex(self, rgb: str) -> None:
        """Output contains only valid hex digits after the ``#``.

        Arrange: A valid ``rgb(R, G, B)`` color string.
        Act: Call ``rgb_to_hex`` with the string.
        Assert: The 6 characters following ``#`` are all valid hex digits (0–9, A–F).

        Args:
            rgb: An ``rgb(R, G, B)`` color string.
        """
        result = rgb_to_hex(rgb)
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", result), f"Invalid hex: {result!r}"

    @given(rgb_color_strategy())
    @settings(max_examples=200)
    def test_roundtrip_channel_values_preserved(self, rgb: str) -> None:
        """Converting ``rgb → hex → rgba`` preserves the original R, G, B values.

        Arrange: A valid ``rgb(R, G, B)`` color string with known channel values.
        Act: Call ``rgb_to_hex`` then ``hex_to_rgba`` on the result.
        Assert: Each R, G, B component in the final ``rgba`` output equals the
            corresponding value from the original input.

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
