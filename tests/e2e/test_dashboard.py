"""E2E tests for the Streamlit Dividend Dashboard.

Requires the app to be running at http://localhost:8501.
Automatically skipped when the server is unreachable.

Test categories:
- TestDividendDashboardSmoke: Verify all major section headings are visible.
- TestDividendDashboardInteractions: Verify controls accept user input.
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
    """Verify all major dashboard sections are visible on page load."""

    def test_page_title_visible(self, dashboard_page: Page) -> None:
        """Verify the 'Dividend Analysis Dashboard' heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="Dividend Analysis Dashboard")).to_be_visible()

    def test_ticker_multiselect_visible(self, dashboard_page: Page) -> None:
        """Verify the ticker multiselect label is visible."""
        expect(dashboard_page.get_by_text("Select tickers to analyze:")).to_be_visible()

    def test_portfolio_overview_section_visible(self, dashboard_page: Page) -> None:
        """Verify the Portfolio Overview section heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="Portfolio Overview")).to_be_visible()

    def test_distribution_breakdown_section_visible(self, dashboard_page: Page) -> None:
        """Verify the Distribution Breakdown section heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="Distribution Breakdown")).to_be_visible()

    def test_growth_calculator_section_visible(self, dashboard_page: Page) -> None:
        """Verify the Dividend Growth Calculator section heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="Dividend Growth Calculator")).to_be_visible()

    def test_drip_calculator_section_visible(self, dashboard_page: Page) -> None:
        """Verify the DRIP Calculator section heading is visible."""
        expect(dashboard_page.get_by_role("heading", name="DRIP Calculator")).to_be_visible()

    def test_distribution_breakdown_caption_visible(self, dashboard_page: Page) -> None:
        """Verify the Distribution Breakdown section caption is visible."""
        expect(
            dashboard_page.get_by_text("View the distribution of received dividend payments across portfolio")
        ).to_be_visible()


# ===========================================================================
# Interaction tests — controls accept input and tiles render
# ===========================================================================


@pytest.mark.e2e
class TestDividendDashboardInteractions:
    """Verify dashboard controls respond to user interaction."""

    def test_drip_shares_input_is_editable(self, dashboard_page: Page) -> None:
        """Verify the Initial Shares input is editable and reflects changes."""
        shares_input = dashboard_page.get_by_label("Initial Shares")
        expect(shares_input).to_be_editable()
        shares_input.fill("50")
        expect(shares_input).to_have_value("50")

    def test_all_default_ticker_tiles_visible(self, dashboard_page: Page) -> None:
        """Verify all default portfolio ticker tiles are visible."""
        for ticker in _DEFAULT_TICKERS:
            expect(dashboard_page.get_by_text(ticker).first).to_be_visible()
