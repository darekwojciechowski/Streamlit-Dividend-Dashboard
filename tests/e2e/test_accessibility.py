"""E2E accessibility tests for the Streamlit Dividend Dashboard.

Runs axe-core against the fully rendered dashboard to detect critical
and serious WCAG violations, and layers keyboard-navigation checks on
top so the suite covers what axe cannot (focus order, focus visibility).

Requires:
    pip install axe-playwright-python
    App running at http://localhost:8501.
"""

import pytest
from playwright.sync_api import Page

from tests.e2e.constants import A11Y_BLOCKING_IMPACTS

try:
    from axe_playwright_python.sync_playwright import Axe

    _AXE_AVAILABLE = True
except ImportError:
    _AXE_AVAILABLE = False


@pytest.mark.e2e
@pytest.mark.a11y
@pytest.mark.critical
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
        blocking = [v for v in violations if v.get("impact") in A11Y_BLOCKING_IMPACTS]
        assert not blocking, f"Found {len(blocking)} critical/serious accessibility violation(s):\n" + "\n".join(
            f"  [{v['impact']}] {v['id']}: {v['description']}" for v in blocking
        )


@pytest.mark.e2e
@pytest.mark.a11y
@pytest.mark.critical
class TestKeyboardNavigation:
    """Verify the dashboard is operable via keyboard alone (WCAG 2.1.1)."""

    def test_first_tab_stop_is_interactive(self, dashboard_page_readonly: Page) -> None:
        """Pressing Tab must land focus on an interactive control, not a decorative element."""
        page = dashboard_page_readonly
        # Streamlit-injected iframes hold keyboard focus by default; start
        # from a deterministic anchor on the page body.
        page.evaluate("document.body.focus()")
        page.keyboard.press("Tab")

        tag_and_role = page.evaluate(
            "() => {"
            "  const el = document.activeElement;"
            "  return { tag: el?.tagName?.toLowerCase() ?? '', role: el?.getAttribute('role') ?? '' };"
            "}"
        )
        interactive_tags = {"a", "button", "input", "select", "textarea", "summary"}
        interactive_roles = {"button", "link", "checkbox", "textbox", "combobox", "option", "menuitem"}

        assert tag_and_role["tag"] in interactive_tags or tag_and_role["role"] in interactive_roles, (
            f"First Tab stop is non-interactive: tag={tag_and_role['tag']!r}, role={tag_and_role['role']!r}"
        )

    def test_focused_element_has_visible_focus_indicator(self, dashboard_page_readonly: Page) -> None:
        """After Tab, the focused element must match :focus-visible (WCAG 2.4.7)."""
        page = dashboard_page_readonly
        page.evaluate("document.body.focus()")
        page.keyboard.press("Tab")

        is_focus_visible = page.evaluate(
            "() => !!document.activeElement && document.activeElement.matches(':focus-visible')"
        )
        assert is_focus_visible, "Active element does not match :focus-visible — keyboard users cannot see focus."
