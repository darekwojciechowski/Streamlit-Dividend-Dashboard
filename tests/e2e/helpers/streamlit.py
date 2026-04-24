"""Streamlit-aware waiting helpers for deterministic E2E assertions.

Streamlit's execution model reruns the whole script on every widget change.
Asserting against DOM state while a rerun is in flight produces flaky reads,
so these helpers block until the UI has settled.
"""

from playwright.sync_api import Page

from tests.e2e.constants import STREAMLIT_IDLE_TIMEOUT_MS


def wait_streamlit_idle(page: Page, timeout: int = STREAMLIT_IDLE_TIMEOUT_MS) -> None:
    """Wait until Streamlit finishes rendering and all spinners have detached.

    Waits for the loading spinner to be absent and, if a status widget
    exists, for it to detach as well. Both waits succeed immediately when
    the elements are already absent.

    Args:
        page: Playwright Page instance.
        timeout: Maximum wait time in milliseconds.
    """
    page.wait_for_selector("[data-testid='stSpinner']", state="detached", timeout=timeout)
    status = page.locator("[data-testid='stStatusWidget']")
    if status.count():
        status.wait_for(state="detached", timeout=timeout)


def wait_for_rerun(page: Page, timeout: int = STREAMLIT_IDLE_TIMEOUT_MS) -> None:
    """Block until a Streamlit rerun triggered by a widget change has settled.

    Event-based replacement for ``page.wait_for_timeout(...)`` after committing
    a widget value. Watches the status widget for *attach → detach* so the
    caller is guaranteed to read post-rerun DOM. Falls back to
    ``wait_streamlit_idle`` when the widget never mounts (fast path when the
    rerun is already over or produced no user-visible status).

    Args:
        page: Playwright Page instance.
        timeout: Maximum wait time in milliseconds.
    """
    status = page.locator("[data-testid='stStatusWidget']")
    try:
        status.first.wait_for(state="attached", timeout=500)
    except Exception:
        wait_streamlit_idle(page, timeout=timeout)
        return

    status.first.wait_for(state="detached", timeout=timeout)
    wait_streamlit_idle(page, timeout=timeout)
