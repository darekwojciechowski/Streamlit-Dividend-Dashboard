"""Shared base for Page Object Model sections.

Centralizes the ``__init__`` + page-scoped wait helper that every section
otherwise redeclares. Sections that need to block on a Streamlit rerun
call :py:meth:`BaseSection._wait_for_rerun`; everything else is a thin
locator layer on top of ``self._page``.
"""

from playwright.sync_api import Page

from tests.e2e.helpers.streamlit import wait_for_rerun, wait_streamlit_idle


class BaseSection:
    """Common page handle for all POM sections."""

    def __init__(self, page: Page) -> None:
        self._page = page

    def _wait_for_rerun(self) -> None:
        """Block until a widget-triggered Streamlit rerun has settled."""
        wait_for_rerun(self._page)

    def _wait_idle(self) -> None:
        """Block until all Streamlit spinners have detached."""
        wait_streamlit_idle(self._page)
