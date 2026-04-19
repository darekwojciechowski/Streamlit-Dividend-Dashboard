"""E2E tests for the Dividend Growth Calculator section (P0.3).

Verifies the full user journey: select a company, set a growth rate, then
read the three Growth Summary metrics and assert their mathematical
relationship (Final = Starting + Total Increase, within floating-point
rounding of ±0.01).

Requires the app to be running at http://localhost:8501.
"""

import pytest
from playwright.sync_api import Page

from tests.e2e.pages.growth_calculator import GrowthCalculatorSection


@pytest.mark.e2e
class TestGrowthCalculator:
    """Verify the Growth Calculator section computes and displays metrics correctly."""

    def test_final_dividend_exceeds_starting_dividend(self, dashboard_page: Page) -> None:
        """Final projected dividend must be greater than the starting dividend.

        Uses the default company and year settings to avoid slow slider
        interaction, but forces growth rate to 10% to ensure measurable change.
        """
        calc = GrowthCalculatorSection(dashboard_page)

        calc.set_growth_rate(10)
        metrics = calc.read_metrics()

        assert metrics["final"] > metrics["starting"], (
            f"Expected final dividend ({metrics['final']}) > starting dividend ({metrics['starting']}) at 10% growth."
        )

    def test_total_increase_equals_final_minus_starting(self, dashboard_page: Page) -> None:
        """Total Increase metric must equal Final − Starting dividend (±0.01).

        Regression guard: if ``calculate_growth_info`` returns an inconsistent
        ``total_increase``, this assertion will fail.
        """
        calc = GrowthCalculatorSection(dashboard_page)

        calc.set_growth_rate(10)
        metrics = calc.read_metrics()

        expected_increase = metrics["final"] - metrics["starting"]
        assert abs(metrics["total_increase"] - expected_increase) <= 0.01, (
            f"Total Increase {metrics['total_increase']:.2f} does not match "
            f"Final − Starting = {expected_increase:.2f} (±0.01)."
        )

    def test_zero_growth_rate_keeps_dividend_flat(self, dashboard_page: Page) -> None:
        """At 0% growth, final dividend must equal the starting dividend."""
        calc = GrowthCalculatorSection(dashboard_page)

        calc.set_growth_rate(0)
        metrics = calc.read_metrics()

        assert abs(metrics["final"] - metrics["starting"]) <= 0.01, (
            f"At 0% growth, final ({metrics['final']:.2f}) should equal starting ({metrics['starting']:.2f})."
        )
