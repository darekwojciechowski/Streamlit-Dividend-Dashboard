"""Page Object Model for the DRIP Calculator section."""

from playwright.sync_api import Locator, Page


class DRIPSection:
    """Encapsulates selectors and actions for the DRIP Calculator section."""

    def __init__(self, page: Page) -> None:
        self._page = page

    # ------------------------------------------------------------------
    # Input locators
    # ------------------------------------------------------------------

    def initial_shares_input(self) -> Locator:
        """Return a locator for the Initial Shares number input."""
        return self._page.get_by_label("Initial Shares")

    def share_price_input(self) -> Locator:
        """Return a locator for the Current Share Price number input."""
        return self._page.get_by_label("Current Share Price ($)")

    def annual_dividend_input(self) -> Locator:
        """Return a locator for the Annual Dividend/Share number input."""
        return self._page.get_by_label("Annual Dividend/Share ($)")

    # ------------------------------------------------------------------
    # Metric card locators (custom HTML rendered by render_metrics_cards)
    # ------------------------------------------------------------------

    def metric_card(self, label: str) -> Locator:
        """Return a locator for a DRIP metric card whose label matches *label*."""
        return self._page.locator(".metric-card").filter(has_text=label)

    def total_return_card(self) -> Locator:
        """Return a locator for the Total Return metric card."""
        return self.metric_card("Total Return")

    def shares_gained_card(self) -> Locator:
        """Return a locator for the Shares Gained metric card."""
        return self.metric_card("Shares Gained")

    def total_dividends_card(self) -> Locator:
        """Return a locator for the Total Dividends metric card."""
        return self.metric_card("Total Dividends")

    def drip_advantage_card(self) -> Locator:
        """Return a locator for the DRIP Advantage metric card."""
        return self.metric_card("DRIP Advantage")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def set_initial_shares(self, shares: int) -> None:
        """Fill Initial Shares with *shares* and commit the value."""
        field = self.initial_shares_input()
        field.click(click_count=3)
        field.fill(str(shares))
        field.press("Tab")

    def set_share_price(self, price: int) -> None:
        """Fill Current Share Price with *price* and commit the value."""
        field = self.share_price_input()
        field.click(click_count=3)
        field.fill(str(price))
        field.press("Tab")

    def set_annual_dividend(self, dividend: int) -> None:
        """Fill Annual Dividend/Share with *dividend* and commit the value."""
        field = self.annual_dividend_input()
        field.click(click_count=3)
        field.fill(str(dividend))
        field.press("Tab")
