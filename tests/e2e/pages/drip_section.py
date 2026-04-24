"""Page Object Model for the DRIP Calculator section."""

from typing import ClassVar

from playwright.sync_api import Locator

from tests.e2e.helpers.parsing import parse_currency
from tests.e2e.pages.base_section import BaseSection


class DRIPSection(BaseSection):
    """Encapsulates selectors and actions for the DRIP Calculator section."""

    # Label → metric-card key mapping. Keys double as invariant names in tests.
    _CARD_LABELS: ClassVar[dict[str, str]] = {
        "Total Return": "total_return",
        "DRIP Advantage": "drip_advantage",
        "Shares Gained": "shares_gained",
        "Total Dividends": "total_dividends",
    }

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
        return self._page.get_by_test_id("drip-metric-card").filter(has_text=label)

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
        self._wait_for_rerun()

    def set_share_price(self, price: int) -> None:
        """Fill Current Share Price with *price* and commit the value."""
        field = self.share_price_input()
        field.click(click_count=3)
        field.fill(str(price))
        field.press("Tab")
        self._wait_for_rerun()

    def set_annual_dividend(self, dividend: int) -> None:
        """Fill Annual Dividend/Share with *dividend* and commit the value."""
        field = self.annual_dividend_input()
        field.click(click_count=3)
        field.fill(str(dividend))
        field.press("Tab")
        self._wait_for_rerun()

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def read_metric_cards(self) -> dict[str, float]:
        """Read and parse all four DRIP metric card values.

        Mirrors :py:meth:`GrowthCalculatorSection.read_metrics` so tests can
        assert financial invariants (e.g. ``shares_gained > 0``) rather than
        visibility alone.

        Returns:
            Dict keyed by invariant name (``total_return``,
            ``drip_advantage``, ``shares_gained``, ``total_dividends``)
            with parsed floats. Missing cards return ``0.0``.
        """
        metrics: dict[str, float] = {}
        for label, key in self._CARD_LABELS.items():
            card = self.metric_card(label)
            value_locator = card.locator(".metric-value").first
            metrics[key] = parse_currency(value_locator.inner_text()) if value_locator.count() else 0.0
        return metrics
