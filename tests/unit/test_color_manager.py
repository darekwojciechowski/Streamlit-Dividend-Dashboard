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
    adjust_gradient,
    apply_wcag_ui_standards,
    determine_text_color_for_dropdown,
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
        assert "(" in result and ")" in result

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
    def test_various_hex_formats_produce_valid_rgb(
        self, hex_color: tuple[str, str]
    ) -> None:
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
        "color,expected_is_light",
        [
            (COLOR_WHITE, True),  # Pure white
            (COLOR_BLACK, False),  # Pure black
            (COLOR_RED, False),  # Red has low luminance
            (COLOR_GREEN, True),  # Green has high luminance (y=0.7152 in RGB)
            (COLOR_BLUE, False),  # Blue has very low luminance (y=0.0722 in RGB)
        ],
    )
    def test_wcag_classification_standard_colors(
        self, color: str, expected_is_light: bool
    ) -> None:
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
        "bg_color,description",
        [
            (COLOR_WHITE, "white"),
            (COLOR_BLACK, "black"),
            (COLOR_RED, "red"),
            (COLOR_GREEN, "green"),
            (COLOR_BLUE, "blue"),
        ],
    )
    def test_contrast_color_selection_all_backgrounds(
        self, bg_color: str, description: str
    ) -> None:
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
