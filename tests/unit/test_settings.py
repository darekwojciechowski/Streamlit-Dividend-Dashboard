"""Unit tests for Settings pydantic-settings class.

Tests cover:
- Default field values when no environment variables are set
- Field validation and type coercion via pydantic
- is_production and is_local property logic
- Override via environment variable injection
- model_config: populate_by_name allows field name access
"""

import pytest
from app.config.app_config import DATA_FILE_PATH
from app.config.settings import Settings

# ============================================================================
# MARKERS
# ============================================================================

pytestmark = pytest.mark.unit


# ============================================================================
# TESTS: Default values
# ============================================================================


class TestSettingsDefaults:
    """Verify all fields have correct defaults when no env vars are set."""

    def test_data_file_path_default(self):
        s = Settings()
        assert s.data_file_path == DATA_FILE_PATH

    def test_environment_default(self):
        s = Settings()
        assert s.environment == "local"

    def test_debug_default(self):
        s = Settings()
        assert s.debug is False


# ============================================================================
# TESTS: Environment overrides
# ============================================================================


class TestSettingsEnvOverrides:
    """Verify env vars or constructor kwargs override defaults correctly."""

    def test_override_data_file_path_via_field_name(self):
        s = Settings(data_file_path="custom/path.csv")
        assert s.data_file_path == "custom/path.csv"

    def test_override_environment_to_production(self):
        s = Settings(environment="production")
        assert s.environment == "production"

    def test_override_debug_to_true(self):
        s = Settings(debug=True)
        assert s.debug is True

    def test_override_via_alias(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "staging")
        s = Settings()
        assert s.environment == "staging"

    def test_override_debug_via_env(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "true")
        s = Settings()
        assert s.debug is True

    def test_override_data_file_path_via_env(self, monkeypatch):
        monkeypatch.setenv("DATA_FILE_PATH", "data/other.csv")
        s = Settings()
        assert s.data_file_path == "data/other.csv"


# ============================================================================
# TESTS: is_production property
# ============================================================================


class TestIsProductionProperty:
    """is_production returns True only for 'production' environment."""

    def test_is_production_when_production(self):
        s = Settings(environment="production")
        assert s.is_production is True

    def test_is_production_case_insensitive(self):
        s = Settings(environment="PRODUCTION")
        assert s.is_production is True

    def test_is_production_false_for_local(self):
        s = Settings(environment="local")
        assert s.is_production is False

    def test_is_production_false_for_staging(self):
        s = Settings(environment="staging")
        assert s.is_production is False

    def test_is_production_false_for_default(self):
        s = Settings()
        assert s.is_production is False


# ============================================================================
# TESTS: is_local property
# ============================================================================


class TestIsLocalProperty:
    """is_local returns True only for 'local' environment."""

    def test_is_local_when_local(self):
        s = Settings(environment="local")
        assert s.is_local is True

    def test_is_local_case_insensitive(self):
        s = Settings(environment="LOCAL")
        assert s.is_local is True

    def test_is_local_false_for_production(self):
        s = Settings(environment="production")
        assert s.is_local is False

    def test_is_local_false_for_staging(self):
        s = Settings(environment="staging")
        assert s.is_local is False

    def test_is_local_true_for_default(self):
        assert Settings().is_local is True


# ============================================================================
# TESTS: Type coercion
# ============================================================================


class TestSettingsTypeCoercion:
    """Pydantic coerces string env var values to declared types."""

    def test_debug_coerced_from_string_false(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "false")
        s = Settings()
        assert s.debug is False

    def test_debug_coerced_from_string_zero(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "0")
        s = Settings()
        assert s.debug is False

    def test_debug_coerced_from_string_one(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "1")
        s = Settings()
        assert s.debug is True
