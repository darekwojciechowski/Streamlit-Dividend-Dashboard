"""E2E smoke, interaction, and chart tests for the Streamlit Dividend Dashboard.

Requires the app to be running at http://localhost:8501.
Automatically skipped when the server is unreachable.

Test categories:
- TestDividendDashboardSmoke: Parametrized heading-visibility checks (class-scoped page).
- TestDividendDashboardInteractions: Controls accept user input and tiles render.
- TestDividendDashboardCharts: Plotly and Nivo chart elements are present.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.constants import SECTION_HEADINGS
from tests.e2e.pages.dashboard_page import DashboardPage
from tests.e2e.pages.drip_section import DRIPSection

# ===========================================================================
# Smoke tests — page renders the expected sections (class-scoped page)
# ===========================================================================


@pytest.mark.e2e
@pytest.mark.smoke
class TestDividendDashboardSmoke:
    """Verify all major dashboard sections are visible on page load."""

    @pytest.mark.parametrize("heading", SECTION_HEADINGS)
    def test_section_heading_is_visible(self, dashboard_page_readonly: Page, heading: str) -> None:
        """Verify a major section heading is visible on the default dashboard view."""
        pom = DashboardPage(dashboard_page_readonly)
        expect(pom.section_heading(heading)).to_be_visible()

    def test_ticker_multiselect_is_visible(self, dashboard_page_readonly: Page) -> None:
        """Verify the ticker multiselect label is visible."""
        pom = DashboardPage(dashboard_page_readonly)
        expect(pom.ticker_multiselect_label()).to_be_visible()

    def test_distribution_breakdown_caption_is_visible(self, dashboard_page_readonly: Page) -> None:
        """Verify the Distribution Breakdown section caption is visible."""
        pom = DashboardPage(dashboard_page_readonly)
        expect(pom.distribution_caption()).to_be_visible()


# ===========================================================================
# Interaction tests — controls accept input and tiles render
# ===========================================================================


@pytest.mark.e2e
class TestDividendDashboardInteractions:
    """Verify dashboard controls respond to user interaction."""

    def test_drip_shares_input_is_editable(self, dashboard_page: Page) -> None:
        """Verify the Initial Shares input is editable and reflects changes."""
        drip = DRIPSection(dashboard_page)
        expect(drip.initial_shares_input()).to_be_editable()
        drip.initial_shares_input().fill("50")
        expect(drip.initial_shares_input()).to_have_value("50")

    def test_all_portfolio_ticker_tiles_visible(self, dashboard_page: Page, portfolio_tickers: list[str]) -> None:
        """Verify all portfolio tickers from the CSV have visible tiles."""
        pom = DashboardPage(dashboard_page)
        for ticker in portfolio_tickers:
            expect(pom.ticker_tile(ticker)).to_be_visible()


# ===========================================================================
# Chart tests — chart elements render
# ===========================================================================


@pytest.mark.e2e
@pytest.mark.charts
class TestDividendDashboardCharts:
    """Verify Plotly and Nivo chart elements are rendered on the dashboard."""

    def test_plotly_chart_is_present(self, dashboard_page_readonly: Page) -> None:
        """Verify at least one Plotly chart container is visible."""
        pom = DashboardPage(dashboard_page_readonly)
        expect(pom.plotly_chart()).to_be_visible()

    def test_plotly_chart_contains_svg(self, dashboard_page_readonly: Page) -> None:
        """Verify the Plotly chart renders an SVG canvas element."""
        pom = DashboardPage(dashboard_page_readonly)
        expect(pom.plotly_chart_svg()).to_be_visible()

    def test_nivo_distribution_chart_is_present(self, dashboard_page_readonly: Page) -> None:
        """Verify the Nivo pie chart custom component is present."""
        pom = DashboardPage(dashboard_page_readonly)
        expect(pom.nivo_chart()).to_be_visible()
