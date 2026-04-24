"""E2E test fixtures for the Streamlit Dividend Dashboard.

Requires the Streamlit app to be running locally on port 8501.
All E2E tests are automatically skipped when the server is unreachable.

To run E2E tests:
    streamlit run main.py
    pytest tests/e2e/ -m e2e
"""

import contextlib
import os
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from playwright.sync_api import Browser, Page

from tests.e2e.constants import (
    BASE_URL,
    DEFAULT_TIMEOUT_MS,
    DESKTOP_1440,
    IPAD_PRO_USER_AGENT,
    IPHONE_13_USER_AGENT,
    MOBILE_IPHONE_13,
    TABLET_IPAD_PRO,
)
from tests.e2e.helpers.streamlit import wait_streamlit_idle

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
        urllib.request.urlopen(BASE_URL, timeout=3)
    except (urllib.error.URLError, OSError):
        pytest.skip(f"Streamlit server not running at {BASE_URL}. Start it first with: streamlit run main.py")


# ---------------------------------------------------------------------------
# Playwright config — pytest-playwright contract fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict[str, Any]) -> dict[str, Any]:
    """Inject launch args so ``HEADED=1`` flips to a visible browser locally.

    Extends the pytest-playwright default so CI still launches headless
    by default. Slow-motion opt-in via ``PW_SLOWMO_MS=<ms>`` helps when
    recording demos or debugging flakes.
    """
    args = {**browser_type_launch_args}
    if os.environ.get("HEADED") == "1":
        args["headless"] = False
    if slowmo := os.environ.get("PW_SLOWMO_MS"):
        with contextlib.suppress(ValueError):
            args["slow_mo"] = int(slowmo)
    return args


@pytest.fixture
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    """Provide a consistent browser context across the suite.

    Sets a deterministic desktop viewport, locale, and timezone so chart
    labels, date formatting, and layout measurements stay stable regardless
    of the developer's machine. Video recording is opt-in via ``PWDEBUG``.
    """
    args = {
        **browser_context_args,
        "viewport": DESKTOP_1440,
        "locale": "en-US",
        "timezone_id": "UTC",
        "ignore_https_errors": True,
    }
    if os.environ.get("PWDEBUG"):
        args["record_video_dir"] = "test-results-e2e/video"
    return args


# ---------------------------------------------------------------------------
# CSV-driven portfolio tickers fixture
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
# Function-scoped page fixture — mutating tests
# ---------------------------------------------------------------------------


@pytest.fixture
def dashboard_page(page: Page) -> Page:
    """Navigate to the dashboard and wait for it to fully render.

    Navigates to the dashboard URL, waits for the Streamlit app root to
    appear, then waits for all spinners and status widgets to detach before
    yielding the page.

    Args:
        page: Playwright Page instance.

    Returns:
        Playwright Page instance ready for testing.
    """
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid='stApp']", state="visible")
    wait_streamlit_idle(page)
    return page


# ---------------------------------------------------------------------------
# Class-scoped page fixture — read-only smoke tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="class")
def dashboard_page_readonly(browser: Browser) -> Iterator[Page]:
    """Navigate to the dashboard once per test class and share the page.

    Suitable for read-only smoke tests that do not mutate UI state.
    Re-using a single page instance across a test class avoids the
    overhead of a full browser navigation per test.

    Args:
        browser: Playwright Browser instance.

    Yields:
        Playwright Page instance ready for testing.
    """
    context = browser.new_context(viewport=DESKTOP_1440, locale="en-US", timezone_id="UTC")
    page = context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid='stApp']", state="visible")
    wait_streamlit_idle(page)
    # Wait for the aria-label patch (injected via components.html) to apply.
    # Ignore if the button doesn't exist in this Streamlit version.
    with contextlib.suppress(Exception):
        page.wait_for_selector(
            '[data-testid="baseButton-headerNoPadding"][aria-label]',
            timeout=5_000,
        )
    yield page
    context.close()


# ---------------------------------------------------------------------------
# Parametrized viewport factory — responsive suite
# ---------------------------------------------------------------------------


_VIEWPORT_PROFILES = {
    "mobile_iphone_13": (MOBILE_IPHONE_13, IPHONE_13_USER_AGENT),
    "tablet_ipad_pro": (TABLET_IPAD_PRO, IPAD_PRO_USER_AGENT),
}


@pytest.fixture(params=sorted(_VIEWPORT_PROFILES), scope="class")
def responsive_page(request: pytest.FixtureRequest, browser: Browser) -> Iterator[Page]:
    """Yield a page rendered at a parametrized device viewport.

    Drives the responsive suite across mobile + tablet profiles without
    duplicating fixture logic per breakpoint.
    """
    viewport, user_agent = _VIEWPORT_PROFILES[request.param]
    context = browser.new_context(viewport=viewport, user_agent=user_agent, locale="en-US", timezone_id="UTC")
    page = context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid='stApp']", state="visible")
    yield page
    context.close()
