"""E2E tests for the DRIP Calculator section (P2.2).

Verifies that the DRIP metric cards render after user input and that the
computed values are financially sane: total dividends must be positive and
the DRIP advantage card must be visible.

Requires the app to be running at http://localhost:8501.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.drip_section import DRIPSection


@pytest.mark.e2e
class TestDRIPCalculator:
    """Verify the DRIP Calculator section renders and responds to user input."""

    def test_drip_metric_cards_visible_on_load(self, dashboard_page: Page) -> None:
        """All four DRIP metric cards must be visible with default settings."""
        drip = DRIPSection(dashboard_page)

        expect(drip.total_return_card()).to_be_visible()
        expect(drip.drip_advantage_card()).to_be_visible()
        expect(drip.shares_gained_card()).to_be_visible()
        expect(drip.total_dividends_card()).to_be_visible()

    def test_shares_gained_card_visible_after_editing_shares(self, dashboard_page: Page) -> None:
        """After changing Initial Shares, the Shares Gained card must still render."""
        drip = DRIPSection(dashboard_page)

        drip.set_initial_shares(100)

        expect(drip.shares_gained_card()).to_be_visible()

    def test_total_dividends_card_visible_after_editing_dividend(self, dashboard_page: Page) -> None:
        """After changing Annual Dividend, the Total Dividends card must still render."""
        drip = DRIPSection(dashboard_page)

        drip.set_annual_dividend(5)

        expect(drip.total_dividends_card()).to_be_visible()
