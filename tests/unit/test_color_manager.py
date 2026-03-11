"""Unit tests for Color Manager utilities.

Tests cover:
- Color format conversions (hex, rgb, rgba)
- Gradient adjustments and brightness modifications
- WCAG luminance calculations for contrast
- Text color determination for accessibility

Test organization:
- Format handling: Various input color formats
- Gradient adjustment: Brightness modifications
- WCAG calculations: Light/dark classification
- Text color: Contrast-safe text colors
- Edge cases: Boundary conditions and malformed inputs
- Consistency: Deterministic behavior

"""

import pytest
from app.utils.color_manager import (
    ColorManager,
    adjust_gradient,
    apply_wcag_ui_standards,
    determine_text_color_for_dropdown,
    hex_to_rgba,
    rgb_to_hex,
)

# ============================================================================
# TEST CONSTANTS - Color hex values used throughout tests
# ============================================================================

# Primary test colors (base RGB + grayscale)
COLOR_BLACK = "#000000"
COLOR_WHITE = "#FFFFFF"
COLOR_RED = "#FF0000"
COLOR_GREEN = "#00FF00"
COLOR_BLUE = "#0000FF"
COLOR_GRAY = "#808080"

# Shorthand formats
COLOR_RED_SHORT = "#F00"
COLOR_WHITE_SHORT = "#FFF"
COLOR_BLACK_SHORT = "#000"

# For RGB format testing
RGB_BLACK = "rgb(0, 0, 0)"
RGB_RED = "rgb(255, 0, 0)"
RGB_RED_SPACED = "rgb( 255 , 0 , 0 )"
RGBA_RED_ALPHA = "rgba(255, 0, 0, 0.5)"

# Default values
DEFAULT_GRADIENT_RGB = "rgb(200, 200, 200)"
TEXT_COLOR_BLACK = "#000000"
TEXT_COLOR_WHITE = "#FFFFFF"

# Mixed case
COLOR_WHITE_MIXED = "#FfFfFf"


def _extract_rgb_values(rgb_string: str) -> list[int]:
    """Extract numeric RGB values from 'rgb(r, g, b)' string.

    Args:
        rgb_string: String in format "rgb(255, 0, 0)"

    Returns:
        list[int]: Three integers [r, g, b]

    Example:
        >>> _extract_rgb_values("rgb(255, 0, 0)")
        [255, 0, 0]
    """
    rgb_values = rgb_string.replace("rgb(", "").replace(")", "").split(",")
    return [int(v.strip()) for v in rgb_values]


@pytest.mark.unit
class TestColorFormatHandling:
    """Test parser handles multiple color input formats."""

    def test_hex_color_converts_to_rgb(self) -> None:
        """Test hex color (#RRGGBB) converts to RGB format."""
        # Arrange
        hex_color = COLOR_RED

        # Act
        result = adjust_gradient(hex_color)

        # Assert
        assert result.startswith("rgb(")
        assert "(" in result
        assert ")" in result

    def test_rgb_color_format_processed(self) -> None:
        """Test RGB color format is recognized and processed."""
        # Arrange
        rgb_color = RGB_RED

        # Act
        result = adjust_gradient(rgb_color)

        # Assert
        assert result.startswith("rgb(")
        assert "255" in result  # Red component preserved

    def test_invalid_color_returns_sensible_default(self) -> None:
        """Test invalid color format returns default gray color."""
        # Arrange
        invalid_color = "not_a_color_format"

        # Act
        result = adjust_gradient(invalid_color)

        # Assert
        assert result == DEFAULT_GRADIENT_RGB


@pytest.mark.unit
class TestGradientAdjustment:
    """Test brightness adjustment for gradient generation."""

    def test_black_adjusted_lighter_than_original(self) -> None:
        """Test that dark colors are brightened by gradient adjustment.

        Black (#000000) should not remain black after adjustment.
        """
        # Arrange
        dark_color = COLOR_BLACK

        # Act
        result = adjust_gradient(dark_color)
        rgb_values = _extract_rgb_values(result)

        # Assert
        assert result != RGB_BLACK  # Should not be unchanged
        assert all(v > 0 for v in rgb_values)  # All components > 0

    def test_white_remains_in_valid_rgb_range(self) -> None:
        """Test brightness adjustment doesn't exceed RGB max (255)."""
        # Arrange
        bright_color = COLOR_WHITE

        # Act
        result = adjust_gradient(bright_color)
        rgb_values = _extract_rgb_values(result)

        # Assert
        assert all(v <= 255 for v in rgb_values), "RGB values must not exceed 255"

    def test_shorthand_hex_expanded_correctly(self) -> None:
        """Test shorthand hex (#RGB) is properly expanded to full gradient."""
        # Arrange
        shorthand = COLOR_RED_SHORT

        # Act
        result = adjust_gradient(shorthand)

        # Assert
        assert result.startswith("rgb(")
        rgb_values = _extract_rgb_values(result)
        assert len(rgb_values) == 3  # Must have R, G, B

    @pytest.mark.parametrize(
        "hex_color",
        [
            (COLOR_RED, "red"),
            (COLOR_GREEN, "green"),
            (COLOR_BLUE, "blue"),
            (COLOR_WHITE_SHORT, "white shorthand"),
            (COLOR_BLACK_SHORT, "black shorthand"),
        ],
    )
    def test_various_hex_formats_produce_valid_rgb(self, hex_color: tuple[str, str]) -> None:
        """Test gradient adjustment works on various color formats.

        Args:
            hex_color: Tuple of (hex_string, description)
        """
        # Act
        result = adjust_gradient(hex_color[0])

        # Assert
        assert result.startswith("rgb(")
        assert ")" in result
        rgb_values = _extract_rgb_values(result)
        assert len(rgb_values) == 3


@pytest.mark.unit
class TestWCAGLuminanceCalculation:
    """Test WCAG 2.0 luminance-based color classification.

    WCAG determines if a color is 'light' or 'dark' by calculating
    relative luminance (0-1 scale). This affects text color contrast.
    """

    def test_white_classified_as_light(self) -> None:
        """Test that white (#FFFFFF) is correctly classified as light."""
        # Act
        result = apply_wcag_ui_standards(COLOR_WHITE)

        # Assert
        assert result is True, "White should be classified as light"

    def test_black_classified_as_dark(self) -> None:
        """Test that black (#000000) is correctly classified as dark."""
        # Act
        result = apply_wcag_ui_standards(COLOR_BLACK)

        # Assert
        assert result is False, "Black should be classified as dark"

    def test_medium_gray_returns_bool(self) -> None:
        """Test that all colors return boolean (light or dark decision)."""
        # Arrange
        medium_gray = COLOR_GRAY

        # Act
        result = apply_wcag_ui_standards(medium_gray)

        # Assert
        assert isinstance(result, bool)

    def test_shorthand_white_classified_light(self) -> None:
        """Test shorthand white (#FFF) classification."""
        # Act
        result = apply_wcag_ui_standards(COLOR_WHITE_SHORT)

        # Assert
        assert result is True

    def test_invalid_hex_defaults_to_light(self) -> None:
        """Test that invalid color hex defaults to light (True).

        When input can't be parsed, function defaults to assuming light
        background for safety (light bg → use dark text).
        """
        # Arrange
        invalid_hex = "#GGGGGG"  # Invalid G characters

        # Act
        result = apply_wcag_ui_standards(invalid_hex)

        # Assert
        assert result is True

    @pytest.mark.parametrize(
        ("color", "expected_is_light"),
        [
            (COLOR_WHITE, True),  # Pure white
            (COLOR_BLACK, False),  # Pure black
            (COLOR_RED, False),  # Red has low luminance
            (COLOR_GREEN, True),  # Green has high luminance (y=0.7152 in RGB)
            (COLOR_BLUE, False),  # Blue has very low luminance (y=0.0722 in RGB)
        ],
    )
    def test_wcag_classification_standard_colors(self, color: str, expected_is_light: bool) -> None:
        """Test WCAG classification on standard CSS colors.

        Args:
            color: Hex color code
            expected_is_light: True if should be classified as light
        """
        # Act
        result = apply_wcag_ui_standards(color)

        # Assert
        assert result is expected_is_light


@pytest.mark.unit
class TestTextColorDetermination:
    """Test WCAG-compliant text color selection for background contrast.

    Determines whether dark (#000000) or light (#FFFFFF) text should be used
    on a given background color for maximum readability and WCAG contrast compliance.
    """

    def test_light_background_uses_dark_text(self) -> None:
        """Test dark text (#000000) is used on light backgrounds.

        White background should use black text for high contrast.
        """
        # Arrange
        light_bg = COLOR_WHITE

        # Act
        result = determine_text_color_for_dropdown(light_bg)

        # Assert
        assert result == TEXT_COLOR_BLACK

    def test_dark_background_uses_light_text(self) -> None:
        """Test light text (#FFFFFF) is used on dark backgrounds.

        Black background should use white text for high contrast.
        """
        # Arrange
        dark_bg = COLOR_BLACK

        # Act
        result = determine_text_color_for_dropdown(dark_bg)

        # Assert
        assert result == TEXT_COLOR_WHITE

    def test_returns_only_valid_text_colors(self) -> None:
        """Test that only valid contrast colors are returned.

        Must always return either pure black or pure white.
        """
        # Arrange
        test_color = COLOR_GRAY

        # Act
        result = determine_text_color_for_dropdown(test_color)

        # Assert
        assert result in [TEXT_COLOR_BLACK, TEXT_COLOR_WHITE]

    @pytest.mark.parametrize(
        ("bg_color", "description"),
        [
            (COLOR_WHITE, "white"),
            (COLOR_BLACK, "black"),
            (COLOR_RED, "red"),
            (COLOR_GREEN, "green"),
            (COLOR_BLUE, "blue"),
        ],
    )
    def test_contrast_color_selection_all_backgrounds(self, bg_color: str, description: str) -> None:
        """Test text color selection works for all test backgrounds.

        Args:
            bg_color: Background hex color
            description: Human-readable color name
        """
        # Act
        result = determine_text_color_for_dropdown(bg_color)

        # Assert
        assert result in [TEXT_COLOR_BLACK, TEXT_COLOR_WHITE]


@pytest.mark.unit
class TestColorEdgeCases:
    """Test boundary conditions and malformed input handling."""

    def test_zero_rgb_components_handled(self) -> None:
        """Test that black (RGB 0,0,0) is handled safely."""
        # Arrange
        black = COLOR_BLACK

        # Act
        result = adjust_gradient(black)

        # Assert
        assert result.startswith("rgb(")
        rgb_values = _extract_rgb_values(result)
        assert all(v >= 0 for v in rgb_values)

    def test_max_rgb_components_handled(self) -> None:
        """Test that white (RGB 255,255,255) stays within bounds."""
        # Arrange
        white = COLOR_WHITE

        # Act
        result = adjust_gradient(white)

        # Assert
        assert result.startswith("rgb(")
        rgb_values = _extract_rgb_values(result)
        assert all(v <= 255 for v in rgb_values)

    def test_mixed_case_hex_normalized(self) -> None:
        """Test mixed case hex (#aBcDeF) is handled correctly."""
        # Arrange
        mixed_case = COLOR_WHITE_MIXED

        # Act
        result = adjust_gradient(mixed_case)

        # Assert
        assert result.startswith("rgb(")

    def test_rgba_with_alpha_channel_extracted(self) -> None:
        """Test RGBA format (with alpha) extracts RGB portion only.

        Should strip alpha channel and process RGB values.
        """
        # Arrange
        rgba = RGBA_RED_ALPHA

        # Act
        result = adjust_gradient(rgba)

        # Assert
        # Should not include alpha: result is rgb(), not rgba()
        assert result.startswith("rgb(")
        assert "rgba" not in result.lower()

    def test_rgb_with_irregular_spacing(self) -> None:
        """Test RGB format tolerates whitespace variations.

        'rgb( 255 , 0 , 0 )' should parse correctly.
        """
        # Arrange
        rgb_spaces = RGB_RED_SPACED

        # Act
        result = adjust_gradient(rgb_spaces)

        # Assert
        assert result.startswith("rgb(")
        rgb_values = _extract_rgb_values(result)
        assert len(rgb_values) == 3


@pytest.mark.unit
class TestColorConsistency:
    """Test deterministic behavior (idempotency and reproducibility)."""

    def test_gradient_adjustment_idempotent(self) -> None:
        """Test that adjusting the same color twice produces identical results.

        RNG-free functions should always return same output for same input.
        """
        # Arrange
        color = COLOR_RED

        # Act
        result1 = adjust_gradient(color)
        result2 = adjust_gradient(color)

        # Assert
        assert result1 == result2

    def test_wcag_calculation_deterministic(self) -> None:
        """Test that WCAG luminance calculation is deterministic.

        Multiple calls with same input must yield same boolean.
        """
        # Arrange
        color = COLOR_GRAY

        # Act - call multiple times
        results = [apply_wcag_ui_standards(color) for _ in range(5)]

        # Assert - all results are identical
        assert len(set(results)) == 1  # All results are the same

    def test_text_color_selection_consistent(self) -> None:
        """Test text color selection gives same result on multiple calls."""
        # Arrange
        bg = "#CCCCCC"

        # Act
        result1 = determine_text_color_for_dropdown(bg)
        result2 = determine_text_color_for_dropdown(bg)
        result3 = determine_text_color_for_dropdown(bg)

        # Assert
        assert result1 == result2 == result3


# ============================================================================
# TESTS: adjust_gradient — uncovered error paths
# ============================================================================


@pytest.mark.unit
class TestAdjustGradientErrorPaths:
    """Cover branches in adjust_gradient not hit by standard tests."""

    def test_hex_with_invalid_length_falls_back_to_default(self) -> None:
        # "#12345" → lstrip → "12345" (5 chars, != 3, != 6) → ValueError at line 31
        result = adjust_gradient("#12345")
        assert result == "rgb(200, 200, 200)"

    def test_hex_with_seven_chars_falls_back_to_default(self) -> None:
        # "#1234567" → lstrip → "1234567" (7 chars) → ValueError at line 31
        result = adjust_gradient("#1234567")
        assert result == "rgb(200, 200, 200)"


# ============================================================================
# TESTS: apply_wcag_ui_standards — invalid length path (line 62)
# ============================================================================


@pytest.mark.unit
class TestWCAGInvalidLengthPath:
    """Cover the raise-inside-try path for wrong-length hex."""

    def test_five_char_hex_after_strip_defaults_to_light(self) -> None:
        # "#ABCDE" → lstrip → "ABCDE" (5 chars, != 3, != 6) → raises at line 62 → returns True
        result = apply_wcag_ui_standards("#ABCDE")
        assert result is True

    def test_two_char_hex_after_strip_defaults_to_light(self) -> None:
        result = apply_wcag_ui_standards("#AB")
        assert result is True


# ============================================================================
# TESTS: hex_to_rgba — uncovered paths (lines 119, 123, 130-131)
# ============================================================================


@pytest.mark.unit
class TestHexToRgba:
    """Cover all branches of hex_to_rgba."""

    def test_standard_hex_produces_rgba(self) -> None:
        result = hex_to_rgba("#FF0000", 0.5)
        assert result == "rgba(255, 0, 0, 0.5)"

    def test_three_char_shorthand_expands_correctly(self) -> None:
        # "#fff" → lstrip → "fff" (len==3) → doubled → "ffffff" → covers line 119
        result = hex_to_rgba("#fff", 1.0)
        assert result == "rgba(255, 255, 255, 1.0)"

    def test_short_hex_red(self) -> None:
        # "#f00" → "f00" → "ff0000"
        result = hex_to_rgba("#f00", 0.8)
        assert result == "rgba(255, 0, 0, 0.8)"

    def test_invalid_length_defaults_to_purple(self) -> None:
        # "#ABCDE" → lstrip → "ABCDE" (5 chars, != 3, != 6) → replaced with "8A2BE2" → covers line 123
        result = hex_to_rgba("#ABCDE", 1.0)
        assert result == "rgba(138, 43, 226, 1.0)"

    def test_invalid_hex_chars_triggers_valueerror_fallback(self) -> None:
        # "GGGGGG" → lstrip("#") = "GGGGGG" (6 chars) → int("GG",16) → ValueError → covers lines 130-131
        result = hex_to_rgba("GGGGGG", 1.0)
        assert result == "rgba(138, 43, 226, 1.0)"

    def test_alpha_value_preserved(self) -> None:
        result = hex_to_rgba("#000000", 0.3)
        assert "0.3" in result


# ============================================================================
# TESTS: rgb_to_hex — error path (lines 149-152)
# ============================================================================


@pytest.mark.unit
class TestRgbToHexErrorPath:
    """Cover the except block in rgb_to_hex."""

    def test_malformed_string_returns_black(self) -> None:
        # "not_valid" → fails strip/split/int parse → covers lines 149-152
        result = rgb_to_hex("not_valid_color")
        assert result == "#000000"

    def test_empty_string_returns_black(self) -> None:
        result = rgb_to_hex("")
        assert result == "#000000"

    def test_valid_rgb_string_converts_correctly(self) -> None:
        result = rgb_to_hex("rgb(102, 197, 204)")
        assert result == "#66C5CC"


# ============================================================================
# TESTS: ColorManager edge cases (lines 184, 188, 201-206)
# ============================================================================


@pytest.mark.unit
class TestColorManagerGetRandomBaseColor:
    """Cover exhausted-pool reset and empty-BASE_COLORS paths."""

    def test_returns_hex_color_string(self) -> None:
        cm = ColorManager()
        color = cm.get_random_base_color()
        assert color.startswith("#")
        assert len(color) == 7

    def test_reset_when_all_colors_exhausted(self) -> None:
        # Directly set used_colors to simulate all exhausted → triggers line 188 reset
        from app.styles.colors_and_styles import BASE_COLORS

        cm = ColorManager()
        cm.used_colors = list(BASE_COLORS)  # mark every color as used
        # Next call should trigger the reset branch (line 188)
        color = cm.get_random_base_color()
        assert color.startswith("#")
        # After reset + one pick, used_colors should have exactly 1 entry
        assert len(cm.used_colors) == 1

    def test_empty_base_colors_returns_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Covers line 184: if not BASE_COLORS → return "#636EFA"
        import app.utils.color_manager as cm_module

        monkeypatch.setattr(cm_module, "BASE_COLORS", [])
        cm = ColorManager()
        result = cm.get_random_base_color()
        assert result == "#636EFA"


@pytest.mark.unit
class TestColorManagerCreateTileHtml:
    """Cover create_tile_html body and the NaN/zero shares branch."""

    def test_positive_shares_renders_html(self) -> None:
        # Covers lines 201-204 truthy branch
        cm = ColorManager()
        html = cm.create_tile_html("AAPL.US", 100.0)
        assert "gradient-tile" in html
        assert "100" in html

    def test_zero_shares_shows_na(self) -> None:
        # Covers line 204 else branch (shares == 0 → "N/A")
        cm = ColorManager()
        html = cm.create_tile_html("AAPL.US", 0.0)
        assert "N/A" in html

    def test_negative_shares_shows_na(self) -> None:
        cm = ColorManager()
        html = cm.create_tile_html("AAPL.US", -5.0)
        assert "N/A" in html

    def test_nan_shares_shows_na(self) -> None:

        cm = ColorManager()
        html = cm.create_tile_html("AAPL.US", float("nan"))
        assert "N/A" in html
