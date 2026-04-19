"""E2E accessibility tests for the Streamlit Dividend Dashboard (P2.1).

Runs axe-core against the fully rendered dashboard to detect critical and
serious WCAG violations. A financial dashboard with colour-coded tiles is a
natural accessibility audit target.

Requires:
    pip install axe-playwright-python
    App running at http://localhost:8501.
"""

import pytest
from playwright.sync_api import Page

try:
    from axe_playwright_python.sync_playwright import Axe

    _AXE_AVAILABLE = True
except ImportError:
    _AXE_AVAILABLE = False


@pytest.mark.e2e
@pytest.mark.skipif(not _AXE_AVAILABLE, reason="axe-playwright-python not installed")
class TestAccessibility:
    """Verify the dashboard meets WCAG accessibility standards via axe-core."""

    def test_dashboard_has_no_critical_a11y_violations(self, dashboard_page_readonly: Page) -> None:
        """Assert zero critical or serious accessibility violations on load.

        axe-core scans the rendered DOM and reports violations by impact level.
        Critical and serious violations block assistive-technology users and must
        be resolved before the suite can pass.
        """
        results = Axe().run(dashboard_page_readonly)
        violations = results.response.get("violations", [])
        critical = [v for v in violations if v.get("impact") in ("critical", "serious")]
        assert not critical, f"Found {len(critical)} critical/serious accessibility violation(s):\n" + "\n".join(
            f"  [{v['impact']}] {v['id']}: {v['description']}" for v in critical
        )
