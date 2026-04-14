"""E2E test fixtures for the Streamlit Dividend Dashboard.

Requires the Streamlit app to be running locally on port 8501.
All E2E tests are automatically skipped when the server is unreachable.

To run E2E tests:
    streamlit run main.py
    pytest tests/e2e/ -m e2e
"""

import urllib.error
import urllib.request

import pytest
from playwright.sync_api import Page

_BASE_URL = "http://localhost:8501"


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
        pytest.skip("Streamlit server not running at http://localhost:8501. Start it first with: streamlit run main.py")


# ---------------------------------------------------------------------------
# Page fixture — navigate and wait for the dashboard to fully render
# ---------------------------------------------------------------------------


@pytest.fixture
def dashboard_page(page: Page) -> Page:
    """Navigate to the dashboard and wait for it to fully render.

    Sets a 15-second default timeout, navigates to the dashboard URL,
    and waits for the network to go idle before yielding the page.

    Args:
        page: Playwright Page instance.

    Returns:
        Playwright Page instance ready for testing.
    """
    page.set_default_timeout(15_000)
    page.goto(_BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid='stApp']", state="visible")
    return page
