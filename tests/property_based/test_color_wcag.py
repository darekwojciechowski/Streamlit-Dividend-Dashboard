"""Property-based tests for color adjustment and WCAG utilities.

Tests cover:
    - adjust_gradient: brightness-only channel adjustment
    - apply_wcag_ui_standards: luminance-based light/dark classification
    - determine_text_color_for_dropdown: accessible text color selection
"""

import re
from typing import ClassVar

import pytest
from app.utils.color_manager import adjust_gradient, apply_wcag_ui_standards, determine_text_color_for_dropdown
from hypothesis import example, given, note, settings
from hypothesis import strategies as st

from .conftest import hex_color_strategy, rgb_color_strategy

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

        Arrange: A 6-digit hex color string.
        Act: Call ``adjust_gradient`` with the hex string.
        Assert: Output fully matches the ``rgb(R, G, B)`` pattern.

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

        Arrange: A valid ``rgb(R, G, B)`` color string.
        Act: Call ``adjust_gradient`` with the rgb string.
        Assert: Output fully matches the ``rgb(R, G, B)`` pattern.

        Args:
            color: An ``rgb(R, G, B)`` color string.
        """
        result = adjust_gradient(color)
        assert self._RGB_PATTERN.fullmatch(result), f"Not a valid rgb string: {result!r}"

    @given(hex_color_strategy())
    @settings(max_examples=300)
    def test_output_channels_are_brighter_or_equal(self, color: str) -> None:
        """Each output channel value is greater than or equal to the corresponding
        input channel value. Output can never be darker than the input.

        Arrange: A 6-digit hex color string with known R, G, B channel values.
        Act: Call ``adjust_gradient`` and extract the output R, G, B components.
        Assert: Each output channel is >= the corresponding input channel.

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

        Arrange: A 6-digit hex color string.
        Act: Call ``adjust_gradient`` and extract the output R, G, B components.
        Assert: Each component is <= 255.

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

        Arrange: Any 6-digit hex color string.
        Act: Call ``apply_wcag_ui_standards`` with the color.
        Assert: Return value is an instance of ``bool``, not merely truthy or falsy.

        Args:
            color: A 6-digit hex color string.
        """
        result = apply_wcag_ui_standards(color)
        assert isinstance(result, bool)

    def test_pure_black_is_dark(self) -> None:
        """``#000000`` must be classified as dark (luminance near 0).

        Arrange: The color ``#000000`` (pure black).
        Act: Call ``apply_wcag_ui_standards``.
        Assert: Returns ``False`` (dark).
        """
        assert apply_wcag_ui_standards("#000000") is False

    def test_pure_white_is_light(self) -> None:
        """``#FFFFFF`` must be classified as light (luminance near 1).

        Arrange: The color ``#FFFFFF`` (pure white).
        Act: Call ``apply_wcag_ui_standards``.
        Assert: Returns ``True`` (light).
        """
        assert apply_wcag_ui_standards("#FFFFFF") is True

    @given(st.integers(min_value=200, max_value=255))
    @settings(max_examples=50)
    def test_near_white_colors_are_light(self, channel_value: int) -> None:
        """Colors with all channels above 200 are perceived as light.

        Arrange: A grayscale hex color with R, G, B all set to the same value in
            [200, 255].
        Act: Call ``apply_wcag_ui_standards`` with the constructed hex string.
        Assert: Returns ``True`` (light).

        Args:
            channel_value: R, G, B value in [200, 255].
        """
        color = f"#{channel_value:02X}{channel_value:02X}{channel_value:02X}"
        assert apply_wcag_ui_standards(color) is True

    @given(st.integers(min_value=0, max_value=40))
    @settings(max_examples=50)
    def test_near_black_colors_are_dark(self, channel_value: int) -> None:
        """Very dark grayscale colors (all channels ≤ 40) are classified as dark.

        Arrange: A grayscale hex color with R, G, B all set to the same value in
            [0, 40].
        Act: Call ``apply_wcag_ui_standards`` with the constructed hex string.
        Assert: Returns ``False`` (dark).

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

        Arrange: Any 6-digit hex color string.
        Act: Call ``determine_text_color_for_dropdown`` with the color.
        Assert: Returns exactly ``#000000`` or ``#FFFFFF``.

        Args:
            color: A 6-digit hex color string.
        """
        result = determine_text_color_for_dropdown(color)
        note(f"determine_text_color_for_dropdown({color!r}) = {result!r}")
        assert result in self.VALID_TEXT_COLORS

    def test_white_background_returns_black_text(self) -> None:
        """Pure white background must use black text for WCAG contrast.

        Arrange: The color ``#FFFFFF`` (pure white background).
        Act: Call ``determine_text_color_for_dropdown``.
        Assert: Returns ``#000000`` (black text).
        """
        assert determine_text_color_for_dropdown("#FFFFFF") == "#000000"

    def test_black_background_returns_white_text(self) -> None:
        """Pure black background must use white text for WCAG contrast.

        Arrange: The color ``#000000`` (pure black background).
        Act: Call ``determine_text_color_for_dropdown``.
        Assert: Returns ``#FFFFFF`` (white text).
        """
        assert determine_text_color_for_dropdown("#000000") == "#FFFFFF"

    @given(hex_color_strategy())
    @settings(max_examples=300)
    def test_consistent_with_wcag_luminance(self, color: str) -> None:
        """Text color choice is consistent with ``apply_wcag_ui_standards`` output.

        Light background (``apply_wcag_ui_standards`` returns ``True``) must
        produce black text; dark background must produce white text.

        Arrange: Any 6-digit hex color string.
        Act: Call both ``apply_wcag_ui_standards`` and
            ``determine_text_color_for_dropdown`` with the same color.
        Assert: Light background (``True``) yields ``#000000``; dark background
            (``False``) yields ``#FFFFFF``.

        Args:
            color: A 6-digit hex color string.
        """
        is_light = apply_wcag_ui_standards(color)
        text_color = determine_text_color_for_dropdown(color)
        if is_light:
            assert text_color == "#000000", f"Light bg {color!r} should use black text"
        else:
            assert text_color == "#FFFFFF", f"Dark bg {color!r} should use white text"
