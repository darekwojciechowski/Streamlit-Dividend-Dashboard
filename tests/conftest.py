"""Shared fixtures and configuration for all tests.

This module provides pytest fixtures for the Streamlit Dividend Dashboard test suite.
Organized in logical sections: session-scoped, sample data, colors/tickers, mocks, and config.

Guidelines:
- Session scope: Expensive resources (test directory setup)
- Module scope: Large datasets, config files
- Function scope (default): Individual test data, temporary files
- Auto-use fixtures: Global test configuration (random seed)

Fixture composition pattern:
- Base fixtures provide raw data (sample_dividend_data)
- Derived fixtures transform data (sample_tsv_file uses sample_dividend_data)
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch
import random
from typing import Generator, Callable


# ============================================================================
# SESSION-SCOPED FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create session-scoped temporary directory for test data.

    This directory persists for the entire test session and should be used
    for large, expensive-to-create test resources.

    Args:
        tmp_path_factory: Pytest factory for session-scoped temporary paths.

    Returns:
        Path: Persistent temp directory for the entire test session.
    """
    return tmp_path_factory.mktemp("test_data")


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_dividend_data() -> pd.DataFrame:
    """Standard dividend dataset for testing.

    Provides a small, clean dataset with 5 rows across 4 tickers (AAPL appears twice).
    Values are already numeric (no ' USD' or '%' suffixes).

    This is a base fixture - use sample_tsv_file for TSV format with suffixes.

    Returns:
        pd.DataFrame: Clean dividend data with columns:
            - Ticker: Symbol with country code (e.g., AAPL.US)
            - Net Dividend: Amount in dollars
            - Tax Collected: Percentage tax taken
            - Shares: Number of shares held
    """
    return pd.DataFrame(
        {
            "Ticker": ["AAPL.US", "MSFT.US", "PKO.PL", "SAP.EU", "AAPL.US"],
            "Net Dividend": [50.0, 75.0, 120.0, 90.0, 55.0],
            "Tax Collected": [10.0, 15.0, 19.0, 18.0, 11.0],
            "Shares": [100, 50, 200, 75, 100],
        }
    )


@pytest.fixture
def single_ticker_data(sample_dividend_data: pd.DataFrame) -> pd.DataFrame:
    """Fixture composition: Single ticker from sample data.

    Filters sample_dividend_data to contain only one unique ticker.
    Useful for testing functions that operate on grouped data.

    Args:
        sample_dividend_data: Base fixture to filter from.

    Returns:
        pd.DataFrame: Rows with only AAPL.US ticker (2 rows).
    """
    return sample_dividend_data[sample_dividend_data["Ticker"] == "AAPL.US"].copy()


@pytest.fixture
def multi_country_data(sample_dividend_data: pd.DataFrame) -> pd.DataFrame:
    """Fixture composition: Data with tickers from different countries.

    Useful for testing currency symbol inference and multi-region analysis.

    Args:
        sample_dividend_data: Base fixture to extract from.

    Returns:
        pd.DataFrame: All rows (contains US, PL, EU country codes).
    """
    return sample_dividend_data.copy()


@pytest.fixture
def sample_tsv_file(tmp_path: Path, sample_dividend_data: pd.DataFrame) -> Path:
    """Fixture composition: TSV file with realistic format (suffixes).

    Creates a properly formatted TSV file mimicking the actual data/dividend_data.csv
    format, with ' USD' suffix in Net Dividend and '%' suffix in Tax Collected.

    This tests the data processor's ability to clean and convert data.

    Args:
        tmp_path: Pytest temporary directory (created fresh per test).
        sample_dividend_data: Base fixture to serialize.

    Returns:
        Path: Absolute path to created TSV file. Each test gets a unique file.
    """
    file_path = tmp_path / "test_dividends.csv"

    df = sample_dividend_data.copy()
    df["Net Dividend"] = df["Net Dividend"].astype(str) + " USD"
    df["Tax Collected"] = df["Tax Collected"].astype(str) + "%"

    df.to_csv(file_path, sep="\t", index=False)
    return file_path


@pytest.fixture
def empty_tsv_file(tmp_path: Path) -> Path:
    """Fixture: Empty TSV file for error condition testing.

    Tests processor behavior when file contains no data rows.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path: Path to empty TSV file (header only).
    """
    file_path = tmp_path / "empty.csv"
    pd.DataFrame().to_csv(file_path, sep="\t", index=False)
    return file_path


@pytest.fixture
def invalid_tsv_file(tmp_path: Path) -> Path:
    """Fixture: TSV with missing required columns for validation testing.

    Tests processor's error handling when input doesn't match schema.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path: Path to TSV file with wrong columns (WrongColumn instead of required ones).
    """
    file_path = tmp_path / "invalid.csv"
    df = pd.DataFrame({"Ticker": ["AAPL.US"], "WrongColumn": [100]})
    df.to_csv(file_path, sep="\t", index=False)
    return file_path


@pytest.fixture
def malformed_tsv_file(tmp_path: Path) -> Path:
    """Fixture: TSV with correct columns but invalid data types.

    Tests processor's coercion and error handling for non-numeric values.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path: Path to TSV with text in numeric columns.
    """
    file_path = tmp_path / "malformed.csv"
    df = pd.DataFrame(
        {
            "Ticker": ["AAPL.US"],
            "Net Dividend": ["not_a_number USD"],
            "Tax Collected": ["invalid%"],
            "Shares": ["fifty"],
        }
    )
    df.to_csv(file_path, sep="\t", index=False)
    return file_path


@pytest.fixture
def edge_case_data() -> pd.DataFrame:
    """Dataset with boundary conditions for robustness testing.

    Includes:
    - Zero values: ZERO.US (0 dividend, 0 tax, 0 shares)
    - NaN/missing: NAN.US (all None values)
    - Negative values: NEG.US (-10 dividend, unusual but valid)
    - Normal values: NORMAL.US (baseline)

    Use this to test error handling and data validation.

    Returns:
        pd.DataFrame: 4 rows with extreme and boundary values.
    """
    return pd.DataFrame(
        {
            "Ticker": ["ZERO.US", "NAN.US", "NEG.US", "NORMAL.US"],
            "Net Dividend": [0.0, None, -10.0, 100.0],
            "Tax Collected": [0.0, None, 5.0, 15.0],
            "Shares": [0, None, 100, 50],
        }
    )


# ============================================================================
# COLOR & TICKER FIXTURES
# ============================================================================


@pytest.fixture
def sample_tickers() -> list[str]:
    """List of sample ticker symbols from different countries.

    Contains one ticker from each supported region:
    - US: AAPL.US (dollar)
    - Europe: SAP.EU (euro)
    - Poland: PKO.PL (Polish zloty)
    - Microsoft: MSFT.US (fallback: dollar)

    Returns:
        list[str]: Sample ticker symbols in alphabetical order.
    """
    return ["AAPL.US", "MSFT.US", "PKO.PL", "SAP.EU"]


@pytest.fixture
def ticker_color_map() -> dict[str, str]:
    """Sample ticker to hex color mapping for visualization.

    Provides a realistic color palette assigned to tickers.
    Colors are from the Pastel palette (high saturation, adjustable brightness).

    Returns:
        dict[str, str]: Maps ticker symbols -> hex color codes.
    """
    return {
        "AAPL.US": "#FF6B6B",  # Pastel red
        "MSFT.US": "#4ECDC4",  # Pastel teal
        "PKO.PL": "#95E1D3",  # Pastel mint
        "SAP.EU": "#FFD93D",  # Pastel yellow
    }


@pytest.fixture
def standard_test_colors() -> dict[str, str]:
    """Standard test colors for color conversion and WCAG testing.

    Contains named colors and their hex equivalents:
    - Black: darkest color (low luminance)
    - White: brightest color (high luminance)
    - Primary colors: RGB values for conversion testing

    Returns:
        dict[str, str]: Color name -> hex code mapping.
    """
    return {
        "black": "#000000",
        "white": "#FFFFFF",
        "red": "#FF0000",
        "green": "#00FF00",
        "blue": "#0000FF",
        "gray": "#808080",
    }


@pytest.fixture(
    params=[
        ("#000000", "black"),
        ("#FFFFFF", "white"),
        ("#FF0000", "red"),
        ("#00FF00", "green"),
        ("#0000FF", "blue"),
    ]
)
def color_hex_pair(request: pytest.FixtureRequest) -> tuple[str, str]:
    """Parametrized fixture: Standard colors for property-based testing.

    Generates test cases for each standard color.
    Use with @pytest.mark.parametrize for exhaustive color testing.

    Args:
        request: Pytest FixtureRequest containing param data.

    Returns:
        tuple[str, str]: (hex_code, color_name) pair.
    """
    return request.param


# ============================================================================
# ============================================================================
# RANDOM SEED (reproducible tests)
# ============================================================================


@pytest.fixture(autouse=True)
def reset_random_seed() -> Generator[None, None, None]:
    """Auto-use fixture ensuring deterministic randomness across runs.

    Resets Python's random seed to 42 before each test, ensuring that
    any random number generation is reproducible. This helps eliminate
    flaky tests caused by randomness.

    Because autouse=True, this runs for every test automatically.
    No need to include it in test function parameters.

    Yields:
        None
    """
    random.seed(42)
    yield


# ============================================================================
# TEST COLLECTION & CONFIGURATION HOOKS
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers for test categorization.

    This hook runs once at test collection time. We register custom markers
    so pytest doesn't warn about unknown markers in test functions.

    Markers defined:
    - @pytest.mark.unit: Fast, isolated tests (< 100ms)
    - @pytest.mark.integration: Slower tests with I/O
    - @pytest.mark.e2e: Full end-to-end workflows
    - @pytest.mark.slow: Tests taking > 1 second
    - @pytest.mark.property: Hypothesis property-based tests
    - @pytest.mark.benchmark: Performance benchmarks

    Usage in tests:
        @pytest.mark.unit
        def test_something():
            ...

    Args:
        config: Pytest configuration object.
    """
    config.addinivalue_line("markers", "unit: Unit tests (isolated, no I/O)")
    config.addinivalue_line("markers", "integration: Integration tests (with I/O)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full workflow)")
    config.addinivalue_line("markers", "slow: Slow tests (> 1s execution time)")
    config.addinivalue_line("markers", "property: Property-based tests (hypothesis)")
    config.addinivalue_line("markers", "benchmark: Performance benchmarks")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Auto-mark tests based on their file location in test suite.

    Automatically applies markers to tests based on where they're located:
    - Tests in tests/unit/* → @pytest.mark.unit
    - Tests in tests/integration/* → @pytest.mark.integration

    This reduces boilerplate - no need to manually mark every test.

    Usage:
        # No marker needed! Auto-marked as @pytest.mark.unit
        # File: tests/unit/test_something.py
        def test_feature():
            ...

    Args:
        config: Pytest configuration object.
        items: List of collected test items to modify.
    """
    for item in items:
        # Auto-mark unit tests (unit/ directory)
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Auto-mark integration tests (integration/ directory)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
