"""Page Object Model for the Dividend Growth Calculator section."""

import re

from playwright.sync_api import Locator, Page


def _parse_currency(text: str) -> float:
    """Strip currency symbols and parse a numeric value from *text*.

    Handles values like '$5.25', '€10.00', 'PLN 3.14'.
    """
    numeric = re.sub(r"[^\d.]", "", text.strip())
    return float(numeric)


class GrowthCalculatorSection:
    """Encapsulates selectors and actions for the Growth Calculator section."""

    def __init__(self, page: Page) -> None:
        self._page = page

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def select_company(self, ticker: str) -> None:
        """Open the company selectbox and choose *ticker*.

        Streamlit renders selectbox as a custom dropdown backed by BaseWeb.
        Clicking the label opens the listbox; then the option is chosen by name.
        """
        self._page.get_by_label("Select company:").click()
        self._page.get_by_role("option", name=ticker, exact=True).click()

    def set_growth_rate(self, pct: int) -> None:
        """Fill the Annual growth (%) number input with *pct* and commit.

        Commits the value via Enter (Streamlit's explicit commit key for
        number_input), then waits for the resulting server rerun to finish
        so downstream metric reads don't see stale DOM.
        """
        field = self._page.get_by_label("Annual growth (%)")
        field.click(click_count=3)
        field.fill(str(pct))
        field.press("Enter")
        self._wait_streamlit_idle()

    def _wait_streamlit_idle(self, timeout: int = 15_000) -> None:
        """Wait for a Streamlit rerun cycle to fully complete.

        A short initial delay lets Streamlit mount the status widget before
        we poll for its detachment — otherwise ``count()`` can return 0 while
        the rerun is still in flight, letting callers read stale metrics.
        """
        self._page.wait_for_timeout(250)
        self._page.wait_for_selector("[data-testid='stSpinner']", state="detached", timeout=timeout)
        status = self._page.locator("[data-testid='stStatusWidget']")
        if status.count():
            status.wait_for(state="detached", timeout=timeout)

    # ------------------------------------------------------------------
    # Metric locators
    # ------------------------------------------------------------------

    def _metric_container(self, label_fragment: str) -> Locator:
        """Return the stMetric container whose label contains *label_fragment*."""
        return self._page.locator("[data-testid='stMetric']").filter(
            has=self._page.locator("[data-testid='stMetricLabel']", has_text=label_fragment)
        )

    def starting_dividend_value(self) -> str:
        """Return the raw text of the Starting Dividend metric value."""
        return self._metric_container("Starting Dividend").locator("[data-testid='stMetricValue']").inner_text()

    def final_dividend_value(self) -> str:
        """Return the raw text of the 'Dividend After N Years' metric value."""
        return self._metric_container("Dividend After").locator("[data-testid='stMetricValue']").inner_text()

    def total_increase_value(self) -> str:
        """Return the raw text of the Total Increase metric value."""
        return self._metric_container("Total Increase").locator("[data-testid='stMetricValue']").inner_text()

    def read_metrics(self) -> dict[str, float]:
        """Read and parse all three Growth Summary metric values.

        Returns:
            Dict with keys ``starting``, ``final``, ``total_increase``
            as parsed floats.
        """
        return {
            "starting": _parse_currency(self.starting_dividend_value()),
            "final": _parse_currency(self.final_dividend_value()),
            "total_increase": _parse_currency(self.total_increase_value()),
        }
