"""E2E tests for the Streamlit Dividend Dashboard.

Requires the app to be running at http://localhost:8501.
Automatically skipped when no server is detected (see conftest.py).

Test categories:
- TestDividendDashboardSmoke   — all major section headings are visible on load
- TestDividendDashboardInteractions — key controls accept user input
"""

import pytest
from playwright.sync_api import Page, expect

# Tickers present in data/dividend_data.csv (default selection = all)
_DEFAULT_TICKERS = ["SBUX.US", "MCD.US", "XTB.PL", "MSFT.US"]


# ===========================================================================
# Smoke tests — page renders the expected sections
# ===========================================================================


@pytest.mark.e2e
class TestDividendDashboardSmoke:
    """Verify that all major sections are visible when the dashboard loads."""

    def test_page_title_visible(self, dashboard_page: Page) -> None:
        """App title 'Dividend Analysis Dashboard' is rendered as a heading."""
        expect(dashboard_page.get_by_role("heading", name="Dividend Analysis Dashboard")).to_be_visible()

    def test_ticker_multiselect_visible(self, dashboard_page: Page) -> None:
        """Ticker multiselect label is present on the page."""
        expect(dashboard_page.get_by_text("Select tickers to analyze:")).to_be_visible()

    def test_portfolio_overview_section_visible(self, dashboard_page: Page) -> None:
        """'Portfolio Overview' section heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="Portfolio Overview")).to_be_visible()

    def test_distribution_breakdown_section_visible(self, dashboard_page: Page) -> None:
        """'Distribution Breakdown' section heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="Distribution Breakdown")).to_be_visible()

    def test_growth_calculator_section_visible(self, dashboard_page: Page) -> None:
        """'Dividend Growth Calculator' section heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="Dividend Growth Calculator")).to_be_visible()

    def test_drip_calculator_section_visible(self, dashboard_page: Page) -> None:
        """'DRIP Calculator' section heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="DRIP Calculator")).to_be_visible()


# ===========================================================================
# Interaction tests — controls accept input and tiles render
# ===========================================================================


@pytest.mark.e2e
class TestDividendDashboardInteractions:
    """Verify that the dashboard controls respond to user interaction."""

    def test_drip_shares_input_is_editable(self, dashboard_page: Page) -> None:
        """DRIP 'Initial Shares' number input is editable and reflects new value."""
        shares_input = dashboard_page.get_by_label("Initial Shares")
        expect(shares_input).to_be_editable()
        shares_input.fill("50")
        expect(shares_input).to_have_value("50")

    def test_all_default_ticker_tiles_visible(self, dashboard_page: Page) -> None:
        """All tickers from the default portfolio appear as tiles on the page."""
        for ticker in _DEFAULT_TICKERS:
            expect(dashboard_page.get_by_text(ticker).first).to_be_visible()
