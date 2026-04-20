"""Page Object Model for the main Dividend Dashboard view."""

from playwright.sync_api import Locator, Page


class DashboardPage:
    """Encapsulates all selectors and actions for the dashboard page."""

    def __init__(self, page: Page) -> None:
        self._page = page

    # ------------------------------------------------------------------
    # Heading / section locators
    # ------------------------------------------------------------------

    def section_heading(self, name: str) -> Locator:
        """Return a locator for a heading element matching *name*."""
        return self._page.get_by_role("heading", name=name)

    def ticker_multiselect_label(self) -> Locator:
        """Return a locator for the ticker multiselect label."""
        return self._page.get_by_text("Select tickers to analyze:")

    def distribution_caption(self) -> Locator:
        """Return a locator for the Distribution Breakdown section caption."""
        return self._page.get_by_text("View the distribution of received dividend payments across portfolio")

    # ------------------------------------------------------------------
    # Portfolio tile locators
    # ------------------------------------------------------------------

    def tiles_container(self) -> Locator:
        """Return a locator for the portfolio tiles container element."""
        return self._page.locator(".tiles-container")

    def ticker_tile(self, ticker: str) -> Locator:
        """Return a locator for a specific ticker tile, scoped to the tiles container.

        Scoping to `.tiles-container` avoids ambiguity when the same ticker
        text appears elsewhere (multiselect tags, calculator selectbox).
        """
        return self._page.locator(".tiles-container").get_by_text(ticker)

    # ------------------------------------------------------------------
    # Chart locators
    # ------------------------------------------------------------------

    def plotly_chart(self) -> Locator:
        """Return a locator for the Plotly chart container."""
        return self._page.locator("[data-testid='stPlotlyChart']").first

    def plotly_chart_svg(self) -> Locator:
        """Return a locator for the SVG element inside the first Plotly chart."""
        return self._page.locator("[data-testid='stPlotlyChart'] .main-svg").first

    def nivo_chart(self) -> Locator:
        """Return a locator for the Nivo custom component (distribution breakdown)."""
        return self._page.locator("[data-testid='stCustomComponentV1']")
