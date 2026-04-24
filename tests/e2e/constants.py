"""Shared constants for the E2E test suite.

Single source of truth for URLs, timeouts, viewport profiles, and section
headings. Test modules and POMs should import from here instead of
redefining values locally.
"""

import pytest

# ---------------------------------------------------------------------------
# Server / timing
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8501"
DEFAULT_TIMEOUT_MS = 15_000
STREAMLIT_IDLE_TIMEOUT_MS = 10_000

# ---------------------------------------------------------------------------
# Section headings (drives smoke + responsive parametrizations)
# ---------------------------------------------------------------------------

SECTION_HEADINGS = [
    pytest.param("Dividend Analysis Dashboard", id="page_title"),
    pytest.param("Portfolio Overview", id="portfolio_overview"),
    pytest.param("Distribution Breakdown", id="distribution_breakdown"),
    pytest.param("Dividend Growth Calculator", id="growth_calculator"),
    pytest.param("DRIP Calculator", id="drip_calculator"),
]

RESPONSIVE_HEADINGS = [
    pytest.param("Dividend Analysis Dashboard", id="page_title"),
    pytest.param("Portfolio Overview", id="portfolio_overview"),
    pytest.param("Dividend Growth Calculator", id="growth_calculator"),
]

# ---------------------------------------------------------------------------
# Viewport profiles — keep aligned with common device breakpoints
# ---------------------------------------------------------------------------

DESKTOP_1440 = {"width": 1440, "height": 900}
TABLET_IPAD_PRO = {"width": 1024, "height": 1366}
MOBILE_IPHONE_13 = {"width": 390, "height": 844}

IPHONE_13_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
)
IPAD_PRO_USER_AGENT = (
    "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
)

# ---------------------------------------------------------------------------
# Accessibility thresholds
# ---------------------------------------------------------------------------

A11Y_BLOCKING_IMPACTS = ("critical", "serious")
