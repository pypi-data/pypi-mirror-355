import logging
from typing import Literal, Optional, Union

from playwright.sync_api import Locator, Page as _Page
from playwright.sync_api import Response

from ._errors import AccessibilityTreeError
from ._network_monitor import PageActivityMonitor
from ._utils import find_element_by_id
from ._utils_sync import (
    add_request_event_listeners_for_page_monitor_shared,
    add_dom_change_listener_shared,
    handle_page_crash,
    determine_load_state_shared,
    get_accessibility_tree,
)
from .constants import (
    DEFAULT_QUERY_ELEMENTS_TIMEOUT_SECONDS,
    DEFAULT_WAIT_FOR_NETWORK_IDLE,
    DEFAULT_INCLUDE_HIDDEN_ELEMENTS,
)
from ..agent.web_agent import WebAgent
from .locator import PromptBasedLocator

log = logging.getLogger("va:playwright")


class Page(_Page):
    def __init__(self, page: _Page, page_monitor: PageActivityMonitor):
        super().__init__(page._impl_obj)
        self.web_agent = WebAgent()
        self._page_monitor = page_monitor

    @classmethod
    def create(cls, page: _Page):
        """
        Creates a new Page instance with a page monitor initialized.

        Parameters:
        -----------
        page (Page): The Playwright page instance.

        Returns:
        --------
        Page: A new instance with a page monitor initialized.
        """
        page_monitor = PageActivityMonitor()
        add_request_event_listeners_for_page_monitor_shared(page, page_monitor)
        add_dom_change_listener_shared(page)
        page.on("crash", handle_page_crash)

        return cls(page, page_monitor)

    def goto(
        self,
        url: str,
        *,
        timeout: Optional[float] = None,
        wait_until: Optional[
            Literal["commit", "domcontentloaded", "load", "networkidle"]
        ] = "domcontentloaded",
        referer: Optional[str] = None,
    ) -> Optional[Response]:
        """
        Override `Page.goto` that uses `domcontentloaded` as the default value for the `wait_until` parameter.
        This change addresses issue with the `load` event not being reliably fired on some websites.

        For parameters information and original method's documentation, please refer to
        [Playwright's documentation](https://playwright.dev/docs/api/class-page#page-goto)
        """
        result = super().goto(
            url=url, timeout=timeout, wait_until=wait_until, referer=referer
        )

        # Redirect will destroy the existing dom change listener, so we need to add it again.
        add_dom_change_listener_shared(self)
        return result

    def get_by_prompt(
        self,
        prompt: str,
        timeout: int = DEFAULT_QUERY_ELEMENTS_TIMEOUT_SECONDS,
        wait_for_network_idle: bool = DEFAULT_WAIT_FOR_NETWORK_IDLE,
        include_hidden: bool = DEFAULT_INCLUDE_HIDDEN_ELEMENTS,
        **kwargs,
    ) -> PromptBasedLocator:
        """
        Returns a PromptBasedLocator that can be used with or without fallback locators

        Parameters:
        -----------
        prompt (str): The natural language description of the element to locate.
        timeout (int) (optional): Timeout value in seconds for the connection with backend API service.
        wait_for_network_idle (bool) (optional): Whether to wait for network reaching full idle state before querying the page. If set to `False`, this method will only check for whether page has emitted [`load` event](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event).
        include_hidden (bool) (optional): Whether to include hidden elements on the page. Defaults to `True`.
        mode (ResponseMode) (optional): The response mode. Can be either `standard` or `fast`. Defaults to `fast`.
        experimental_query_elements_enabled (bool) (optional): Whether to use the experimental implementation of the query elements feature. Defaults to `False`.

        Returns:
        --------
        PromptBasedLocator: A locator that uses prompt-based element finding
        """
        return PromptBasedLocator(self, prompt)

    def _get_locator_by_prompt(
        self,
        prompt: str,
        wait_for_network_idle: bool = DEFAULT_WAIT_FOR_NETWORK_IDLE,
        include_hidden: bool = DEFAULT_INCLUDE_HIDDEN_ELEMENTS,
    ) -> Union[Locator, None]:
        """
        Internal method to get element by prompt - used by PromptBasedLocator

        Returns:
        --------
        Playwright [Locator](https://playwright.dev/python/docs/api/class-locator) | None: The found element or `None` if no matching elements were found.
        """
        self.wait_for_page_ready_state(wait_for_network_idle=wait_for_network_idle)

        try:
            accessibility_tree = get_accessibility_tree(self, include_hidden)
        except Exception as e:
            raise AccessibilityTreeError() from e

        log.info(accessibility_tree)
        element = self.web_agent.query_element(
            prompt, accessibility_tree=accessibility_tree
        )

        if not element:
            return None

        web_element = find_element_by_id(
            page=self, tf623_id=element.id, iframe_path=element.iframe_path
        )

        return web_element  # type: ignore

    def wait_for_page_ready_state(
        self, wait_for_network_idle: bool = DEFAULT_WAIT_FOR_NETWORK_IDLE
    ):
        """
        Waits for the page to reach the "Page Ready" state, i.e. page has entered a relatively stable state and most main content is loaded. Might be useful before triggering an query or any other interaction for slowly rendering pages.

        Parameters:
        -----------
        wait_for_network_idle (bool) (optional): Whether to wait for network reaching full idle state. If set to `False`, this method will only check for whether page has emitted [`load` event](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event).
        """
        log.debug(f"Waiting for {self} to reach 'Page Ready' state")

        # Wait for the page to reach the "Page Ready" state
        determine_load_state_shared(
            page=self,
            monitor=self._page_monitor,
            wait_for_network_idle=wait_for_network_idle,
        )

        # Reset the page monitor after the page is ready
        if self._page_monitor:
            self._page_monitor.reset()

        log.debug(f"Finished waiting for {self} to reach 'Page Ready' state")
