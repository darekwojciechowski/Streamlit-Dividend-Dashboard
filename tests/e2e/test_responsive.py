"""E2E responsive / mobile tests for the Streamlit Dividend Dashboard.

Verifies that primary section headings remain visible across mobile and
tablet viewport profiles. The ``responsive_page`` fixture (in
``conftest.py``) parametrizes over device profiles so every test in this
file runs on every profile automatically.

Requires the app to be running at http://localhost:8501.

Usage:
    pytest tests/e2e/test_responsive.py -m responsive
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.constants import RESPONSIVE_HEADINGS
from tests.e2e.pages.dashboard_page import DashboardPage


@pytest.mark.e2e
@pytest.mark.responsive
class TestResponsiveLayout:
    """Verify primary headings are visible across mobile + tablet viewports."""

    @pytest.mark.parametrize("heading", RESPONSIVE_HEADINGS)
    def test_section_heading_visible(self, responsive_page: Page, heading: str) -> None:
        """Assert a primary heading is visible at the parametrized viewport."""
        pom = DashboardPage(responsive_page)
        expect(pom.section_heading(heading)).to_be_visible()
