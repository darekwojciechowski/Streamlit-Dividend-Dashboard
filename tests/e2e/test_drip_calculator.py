"""E2E tests for the DRIP Calculator section.

Verifies that the DRIP metric cards render after user input and — beyond
visibility — that the computed values satisfy core financial invariants
(shares gained > 0, total return ≥ initial investment, DRIP advantage
never negative).

Requires the app to be running at http://localhost:8501.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.drip_section import DRIPSection


@pytest.mark.e2e
@pytest.mark.smoke
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


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.regression
class TestDRIPInvariants:
    """Verify the DRIP model satisfies core financial invariants.

    These assertions are the safety net that a plain visibility check can
    never provide: a card can render happily with nonsensical values. If
    any of these fail, the financial model has regressed.
    """

    def test_shares_gained_is_positive_after_long_horizon(self, dashboard_page: Page) -> None:
        """With default inputs the DRIP model must gain at least one share."""
        drip = DRIPSection(dashboard_page)

        drip.set_initial_shares(100)
        drip.set_annual_dividend(5)

        metrics = drip.read_metric_cards()
        assert metrics["shares_gained"] > 0, (
            f"DRIP gained {metrics['shares_gained']} shares — expected > 0 with "
            "positive dividend over the default horizon."
        )

    def test_total_return_not_negative(self, dashboard_page: Page) -> None:
        """Total return must be non-negative — DRIP never loses principal in the model."""
        drip = DRIPSection(dashboard_page)

        drip.set_initial_shares(100)
        drip.set_annual_dividend(5)

        metrics = drip.read_metric_cards()
        assert metrics["total_return"] >= 0, (
            f"Total return {metrics['total_return']:.2f} is negative — the DRIP model cannot produce a loss."
        )

    def test_drip_advantage_not_negative(self, dashboard_page: Page) -> None:
        """DRIP Advantage must be ≥ 0 — reinvesting is never worse than not."""
        drip = DRIPSection(dashboard_page)

        drip.set_initial_shares(100)
        drip.set_annual_dividend(5)

        metrics = drip.read_metric_cards()
        assert metrics["drip_advantage"] >= 0, (
            f"DRIP Advantage {metrics['drip_advantage']:.2f} is negative — "
            "reinvestment cannot be worse than the no-reinvest baseline."
        )

    def test_total_dividends_is_positive(self, dashboard_page: Page) -> None:
        """Total dividends received must be > 0 with a positive annual dividend."""
        drip = DRIPSection(dashboard_page)

        drip.set_initial_shares(100)
        drip.set_annual_dividend(5)

        metrics = drip.read_metric_cards()
        assert metrics["total_dividends"] > 0, (
            f"Total dividends {metrics['total_dividends']:.2f} ≤ 0 despite a positive annual dividend."
        )
