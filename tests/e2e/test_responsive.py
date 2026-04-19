"""E2E responsive / mobile tests for the Streamlit Dividend Dashboard (P3.2).

Verifies that primary section headings remain visible on a mobile viewport
using the iPhone 13 device profile. One or two responsive tests signal
layout maturity to reviewers.

Requires the app to be running at http://localhost:8501.

Usage:
    pytest tests/e2e/test_responsive.py -m e2e
"""

import pytest
from playwright.sync_api import Browser, Page, expect

from tests.e2e.pages.dashboard_page import DashboardPage

_BASE_URL = "http://localhost:8501"

_IPHONE_13_VIEWPORT = {"width": 390, "height": 844}
_IPHONE_13_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
)

RESPONSIVE_HEADINGS = [
    pytest.param("Dividend Analysis Dashboard", id="page_title"),
    pytest.param("Portfolio Overview", id="portfolio_overview"),
    pytest.param("Dividend Growth Calculator", id="growth_calculator"),
]


@pytest.fixture(scope="class")
def mobile_page(browser: Browser) -> Page:
    """Yield a page rendered at iPhone 13 viewport dimensions.

    Creates a separate browser context with mobile viewport and user-agent
    so the responsive tests are isolated from the desktop suite.
    """
    context = browser.new_context(
        viewport=_IPHONE_13_VIEWPORT,
        user_agent=_IPHONE_13_USER_AGENT,
    )
    page = context.new_page()
    page.set_default_timeout(15_000)
    page.goto(_BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid='stApp']", state="visible")
    yield page
    context.close()


@pytest.mark.e2e
class TestResponsiveLayout:
    """Verify primary headings are visible on a mobile (iPhone 13) viewport."""

    @pytest.mark.parametrize("heading", RESPONSIVE_HEADINGS)
    def test_section_heading_visible_on_mobile(self, mobile_page: Page, heading: str) -> None:
        """Assert a primary heading is visible at mobile viewport width."""
        pom = DashboardPage(mobile_page)
        expect(pom.section_heading(heading)).to_be_visible()
