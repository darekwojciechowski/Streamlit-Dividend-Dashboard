"""E2E test fixtures for the Streamlit Dividend Dashboard.

These tests require the Streamlit app to be running locally on port 8501.
All E2E tests are automatically skipped when no server is detected.

To run E2E tests locally:
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
    """Skip all E2E tests when the Streamlit server is not reachable.

    Performs a single HTTP probe at session start so the server is only
    checked once per pytest run, adding negligible overhead to normal
    unit/integration runs.
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
    """Return a Playwright Page that has navigated to the loaded dashboard.

    Sets a generous default timeout (15 s) to accommodate Streamlit's
    server-side rendering and WebSocket initialisation, then waits for
    the network to go idle before yielding the page to the test.
    """
    page.set_default_timeout(15_000)
    page.goto(_BASE_URL)
    page.wait_for_load_state("networkidle")
    return page
