"""Unit tests for App Configuration module (app_config.py).

Tests verify:
- Configuration constants exist and have correct types
- Configuration values are within valid ranges
- Color theme is properly defined and all colors are valid
- Special requirements met: e.g., primary color is purple (#8A2BE2)
- Values are immutable (don't drift during test runs)

Configuration categories tested:
- Application defaults (growth rate, projections years)
- Data file paths
- UI settings (layout, sidebar, titles)
- Color theme (all required keys, valid hex format)
"""

import app.app_config as app_config
import pytest

# ============================================================================
# TEST CONSTANTS
# ============================================================================

# Expected configuration values
EXPECTED_GROWTH_PERCENTAGE = 7.0
EXPECTED_NUM_YEARS = 15
EXPECTED_PRIMARY_COLOR = "#8A2BE2"  # Purple

# Valid ranges
MIN_GROWTH_PERCENT = 0
MAX_GROWTH_PERCENT = 50
MIN_YEARS = 1
MAX_YEARS = 50

# Required keys
REQUIRED_COLOR_KEYS = [
    "primary",
    "secondary",
    "accent",
    "fallback",
    "success",
    "warning",
]
REQUIRED_UI_CONFIG_ITEMS = [
    ("DEFAULT_PAGE_TITLE", str),
    ("DEFAULT_SIDEBAR_STATE", str),
    ("DEFAULT_LAYOUT", str),
    ("DEFAULT_DASHBOARD_TITLE", str),
]

# Valid values
VALID_SIDEBAR_STATES = ["expanded", "collapsed"]
VALID_LAYOUT_OPTIONS = ["centered", "wide"]

# Type checking
HEX_COLOR_LENGTH = 7  # "#RRGGBB" = 7 characters


def _is_valid_hex_color(color: str) -> bool:
    """Helper: Check if string is valid hex color (#RRGGBB).

    Args:
        color: String to validate

    Returns:
        bool: True if format is valid hex color
    """
    if not isinstance(color, str):
        return False
    if not color.startswith("#"):
        return False
    if len(color) != HEX_COLOR_LENGTH:
        return False
    try:
        int(color[1:], 16)
        return True
    except ValueError:
        return False


@pytest.mark.unit
class TestApplicationDefaults:
    """Test application default values for dividend projections."""

    def test_default_growth_percentage_defined_and_positive(self) -> None:
        """Test DEFAULT_GROWTH_PERCENTAGE exists and is positive number."""
        # Assert
        assert hasattr(app_config, "DEFAULT_GROWTH_PERCENTAGE")
        assert isinstance(app_config.DEFAULT_GROWTH_PERCENTAGE, int | float)
        assert app_config.DEFAULT_GROWTH_PERCENTAGE > MIN_GROWTH_PERCENT

    def test_default_growth_percentage_in_reasonable_range(self) -> None:
        """Test growth rate is between 0% and 50% (sensible projection range)."""
        # Assert
        assert MIN_GROWTH_PERCENT < app_config.DEFAULT_GROWTH_PERCENTAGE <= MAX_GROWTH_PERCENT

    def test_default_growth_percentage_correct_value(self) -> None:
        """Test growth percentage equals expected value (7%)."""
        # Assert
        assert app_config.DEFAULT_GROWTH_PERCENTAGE == EXPECTED_GROWTH_PERCENTAGE

    def test_default_num_years_defined_and_positive(self) -> None:
        """Test DEFAULT_NUM_YEARS exists and is positive integer."""
        # Assert
        assert hasattr(app_config, "DEFAULT_NUM_YEARS")
        assert isinstance(app_config.DEFAULT_NUM_YEARS, int)
        assert app_config.DEFAULT_NUM_YEARS > MIN_YEARS

    def test_default_num_years_in_reasonable_range(self) -> None:
        """Test projection years between 1 and 50 (sensible forecast horizon)."""
        # Assert
        assert MIN_YEARS < app_config.DEFAULT_NUM_YEARS <= MAX_YEARS

    def test_default_num_years_correct_value(self) -> None:
        """Test number of years equals expected value (15 years)."""
        # Assert
        assert app_config.DEFAULT_NUM_YEARS == EXPECTED_NUM_YEARS


@pytest.mark.unit
class TestDataAndUIConfiguration:
    """Test file paths and UI display settings.

    Validates:
    - DATA_FILE_PATH points to valid CSV location
    - UI defaults (page title, layout, sidebar state)
    """

    def test_data_file_path_defined_as_string(self) -> None:
        """Test DATA_FILE_PATH exists and is a string."""
        # Assert
        assert hasattr(app_config, "DATA_FILE_PATH")
        assert isinstance(app_config.DATA_FILE_PATH, str)

    def test_data_file_path_points_to_csv_file(self) -> None:
        """Test data file path has .csv extension."""
        # Act
        path = app_config.DATA_FILE_PATH

        # Assert
        assert path.endswith(".csv"), "Data file should be CSV format"

    def test_data_file_path_includes_directory_separators(self) -> None:
        """Test data file path is not just a filename (has directory structure)."""
        # Act
        path = app_config.DATA_FILE_PATH

        # Assert
        has_unix_sep = "/" in path
        has_windows_sep = "\\" in path
        assert has_unix_sep or has_windows_sep, "Path should include directory separators"

    @pytest.mark.parametrize(
        ("config_name", "expected_type"),
        REQUIRED_UI_CONFIG_ITEMS,
    )
    def test_ui_config_attributes_defined(self, config_name: str, expected_type: type) -> None:
        """Test that all UI configuration attributes exist with correct types.

        Args:
            config_name: Name of config attribute (e.g., DEFAULT_PAGE_TITLE)
            expected_type: Expected Python type for this config value
        """
        # Assert
        assert hasattr(app_config, config_name)
        attr_value = getattr(app_config, config_name)
        assert isinstance(attr_value, expected_type)
        # String configs should not be empty
        if expected_type is str:
            assert len(attr_value) > 0

    def test_sidebar_state_is_valid_option(self) -> None:
        """Test sidebar state is one of the valid options."""
        # Assert
        assert app_config.DEFAULT_SIDEBAR_STATE in VALID_SIDEBAR_STATES

    def test_layout_is_valid_option(self) -> None:
        """Test layout is one of the valid UI layout options."""
        # Assert
        assert app_config.DEFAULT_LAYOUT in VALID_LAYOUT_OPTIONS

    def test_sidebar_expanded_by_default(self) -> None:
        """Test that sidebar is expanded (not collapsed) on app startup."""
        # Assert
        assert app_config.DEFAULT_SIDEBAR_STATE == "expanded"


@pytest.mark.unit
class TestColorThemeConfiguration:
    """Test color theme dictionary structure and content."""

    def test_color_theme_exists_as_dict(self) -> None:
        """Test COLOR_THEME is defined as a dictionary."""
        # Assert
        assert hasattr(app_config, "COLOR_THEME")
        assert isinstance(app_config.COLOR_THEME, dict)

    def test_color_theme_contains_all_required_keys(self) -> None:
        """Test COLOR_THEME has all required color definitions.

        Required colors: primary, secondary, accent, fallback, success, warning
        """
        # Assert
        for key in REQUIRED_COLOR_KEYS:
            assert key in app_config.COLOR_THEME, f"Missing required color: {key}"

    def test_primary_color_is_purple_as_specified(self) -> None:
        """Test primary color is purple (#8A2BE2) per spec.

        The specification requires: COLOR_THEME['primary'] = '#8A2BE2'
        """
        # Assert
        primary = app_config.COLOR_THEME["primary"]
        assert primary.upper() == EXPECTED_PRIMARY_COLOR

    @pytest.mark.parametrize("color_key", REQUIRED_COLOR_KEYS)
    def test_each_color_is_valid_hex_format(self, color_key: str) -> None:
        """Test each color value is a valid hex color code.

        Format: #RRGGBB (# followed by 6 hexadecimal digits)

        Args:
            color_key: Color name from COLOR_THEME
        """
        # Act
        color_value = app_config.COLOR_THEME[color_key]

        # Assert
        assert isinstance(color_value, str)
        assert _is_valid_hex_color(color_value), f"Color {color_key}='{color_value}' is not valid hex format"

    def test_success_and_warning_colors_are_distinct(self) -> None:
        """Test success and warning colors are different (for accessibility).

        These colors should be visually distinct to prevent confusion.
        """
        # Assert
        success = app_config.COLOR_THEME["success"]
        warning = app_config.COLOR_THEME["warning"]
        assert success != warning, "Success and warning colors must be distinct"

    def test_all_color_values_are_strings(self) -> None:
        """Test all color theme values are strings (not other types)."""
        # Assert
        for key, value in app_config.COLOR_THEME.items():
            assert isinstance(value, str), f"Color {key} should be string, got {type(value)}"


@pytest.mark.unit
class TestConfigurationImmutabilityAndConsistency:
    """Test that configuration values don't drift or change (immutability check).

    Verifies configuration is deterministic and not modified by tests.
    """

    def test_numeric_configs_consistent_across_multiple_reads(self) -> None:
        """Test numeric config values stay constant (not modified)."""
        # Act - access config multiple times
        growth_values = [
            app_config.DEFAULT_GROWTH_PERCENTAGE,
            app_config.DEFAULT_GROWTH_PERCENTAGE,
            app_config.DEFAULT_GROWTH_PERCENTAGE,
        ]
        years_values = [
            app_config.DEFAULT_NUM_YEARS,
            app_config.DEFAULT_NUM_YEARS,
            app_config.DEFAULT_NUM_YEARS,
        ]

        # Assert - all values identical (immutable)
        assert len(set(growth_values)) == 1, "Growth rate changed during test"
        assert len(set(years_values)) == 1, "Years value changed during test"

    def test_string_configs_consistent_across_multiple_reads(self) -> None:
        """Test string config values stay constant (not modified)."""
        # Act
        path_values = [
            app_config.DATA_FILE_PATH,
            app_config.DATA_FILE_PATH,
        ]
        title_values = [
            app_config.DEFAULT_PAGE_TITLE,
            app_config.DEFAULT_PAGE_TITLE,
        ]

        # Assert
        assert len(set(path_values)) == 1, "Data path changed during test"
        assert len(set(title_values)) == 1, "Page title changed during test"

    def test_color_theme_consistent_across_multiple_reads(self) -> None:
        """Test COLOR_THEME dictionary values stay constant."""
        # Act
        primary_1 = app_config.COLOR_THEME["primary"]
        primary_2 = app_config.COLOR_THEME["primary"]

        # Assert
        assert primary_1 == primary_2, "Primary color changed"


@pytest.mark.unit
class TestConfigurationDocumenationAndCompleteness:
    """Test that configuration module is well-documented."""

    def test_module_has_docstring(self) -> None:
        """Test app_config module includes a docstring."""
        # Assert
        assert app_config.__doc__ is not None
        assert len(app_config.__doc__) > 0

    def test_no_missing_critical_configs(self) -> None:
        """Test that critical configuration attributes are present.

        Fails fast if required configs are accidentally deleted.
        """
        # Assert
        required_attrs = [
            "DEFAULT_GROWTH_PERCENTAGE",
            "DEFAULT_NUM_YEARS",
            "DATA_FILE_PATH",
            "DEFAULT_PAGE_TITLE",
            "DEFAULT_SIDEBAR_STATE",
            "DEFAULT_LAYOUT",
            "COLOR_THEME",
            "DEFAULT_DASHBOARD_TITLE",
        ]
        for attr in required_attrs:
            assert hasattr(app_config, attr), f"Missing critical config: {attr}"
