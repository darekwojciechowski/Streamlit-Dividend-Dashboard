"""E2E tests for ticker filtering behaviour (P0.2).

Verifies the empty-state path: when a user deselects all tickers the app
must render the info message and the portfolio tiles container must vanish.

Requires the app to be running at http://localhost:8501.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.dashboard_page import DashboardPage


@pytest.mark.e2e
class TestTickerFiltering:
    """Verify the dashboard responds correctly when ticker selection changes."""

    def test_empty_state_shown_when_all_tickers_deselected(self, dashboard_page: Page) -> None:
        """Deselecting all tickers must show the empty-state info message.

        Regression guard: if the ``st.info("Select tickers to view analysis.")``
        branch in ``main.py`` is removed or changed, this test must fail.
        """
        pom = DashboardPage(dashboard_page)

        pom.clear_all_tickers()

        expect(pom.empty_state_message()).to_be_visible()

    def test_tiles_absent_when_all_tickers_deselected(self, dashboard_page: Page) -> None:
        """Deselecting all tickers must hide the portfolio tiles container."""
        pom = DashboardPage(dashboard_page)

        pom.clear_all_tickers()

        expect(pom.tiles_container()).not_to_be_visible()
