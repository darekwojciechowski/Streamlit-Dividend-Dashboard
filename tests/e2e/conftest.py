"""E2E test fixtures for the Streamlit Dividend Dashboard.

Requires the Streamlit app to be running locally on port 8501.
All E2E tests are automatically skipped when the server is unreachable.

To run E2E tests:
    streamlit run main.py
    pytest tests/e2e/ -m e2e
"""

import contextlib
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
import pytest
from playwright.sync_api import Browser, Page

_BASE_URL = "http://localhost:8501"
_DATA_FILE = Path("data/dividend_data.csv")


# ---------------------------------------------------------------------------
# Session-level guard — skip entire E2E session when app is not running
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _require_live_server() -> None:
    """Skip E2E tests if the Streamlit server is unreachable.

    Performs a single HTTP probe at session start. The server is checked
    once per pytest run, adding negligible overhead to unit/integration runs.
    """
    try:
        urllib.request.urlopen(_BASE_URL, timeout=3)
    except (urllib.error.URLError, OSError):
        pytest.skip(f"Streamlit server not running at {_BASE_URL}. Start it first with: streamlit run main.py")


# ---------------------------------------------------------------------------
# CSV-driven portfolio tickers fixture (P1.2)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def portfolio_tickers() -> list[str]:
    """Return a sorted list of unique tickers read from the portfolio CSV.

    Drives tile-visibility tests from the actual data file instead of a
    hardcoded constant, so adding a ticker to the CSV is automatically
    covered without touching test code.
    """
    df = pd.read_csv(_DATA_FILE, sep="\t")
    return sorted(df["Ticker"].unique().tolist())


# ---------------------------------------------------------------------------
# Streamlit idle helper (P1.3)
# ---------------------------------------------------------------------------


def _wait_streamlit_idle(page: Page, timeout: int = 10_000) -> None:
    """Wait until Streamlit finishes rendering and all spinners have detached.

    Waits for the absence of the loading spinner and, if a status widget
    is present, waits for it to detach as well. Both waits succeed
    immediately when the elements are already absent.

    Args:
        page: Playwright Page instance.
        timeout: Maximum wait time in milliseconds.
    """
    page.wait_for_selector("[data-testid='stSpinner']", state="detached", timeout=timeout)
    status = page.locator("[data-testid='stStatusWidget']")
    if status.count():
        status.wait_for(state="detached", timeout=timeout)


# ---------------------------------------------------------------------------
# Function-scoped page fixture — mutating tests
# ---------------------------------------------------------------------------


@pytest.fixture
def dashboard_page(page: Page) -> Page:
    """Navigate to the dashboard and wait for it to fully render.

    Sets a 15-second default timeout, navigates to the dashboard URL,
    waits for the Streamlit app root to appear, then waits for all
    spinners and status widgets to detach before yielding the page.

    Args:
        page: Playwright Page instance.

    Returns:
        Playwright Page instance ready for testing.
    """
    page.set_default_timeout(15_000)
    page.goto(_BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid='stApp']", state="visible")
    _wait_streamlit_idle(page)
    return page


# ---------------------------------------------------------------------------
# Class-scoped page fixture — read-only smoke tests (P3.3)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="class")
def dashboard_page_readonly(browser: Browser) -> Page:
    """Navigate to the dashboard once per test class and share the page.

    Suitable for read-only smoke tests that do not mutate UI state.
    Re-using a single page instance across a test class avoids the
    overhead of a full browser navigation per test.

    Args:
        browser: Playwright Browser instance (class-scoped by default in
            pytest-playwright when requested at this scope level).

    Yields:
        Playwright Page instance ready for testing.
    """
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(15_000)
    page.goto(_BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid='stApp']", state="visible")
    _wait_streamlit_idle(page)
    # Wait for the aria-label patch (injected via components.html) to apply.
    # Ignore if the button doesn't exist in this Streamlit version.
    with contextlib.suppress(Exception):
        page.wait_for_selector(
            '[data-testid="baseButton-headerNoPadding"][aria-label]',
            timeout=5_000,
        )
    yield page
    context.close()
