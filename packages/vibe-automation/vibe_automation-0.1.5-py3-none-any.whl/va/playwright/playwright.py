from contextlib import contextmanager
import os
from playwright.sync_api import sync_playwright, Page as PlaywrightPage, Browser
from .page import Page as VibePage


class WrappedBrowser:
    """Browser wrapper that automatically wraps pages with VibePage functionality."""
    
    def __init__(self, browser: Browser):
        self._browser = browser
    
    def new_page(self, **kwargs) -> VibePage:
        """Create a new page and automatically wrap it with VibePage functionality."""
        page = self._browser.new_page(**kwargs)
        return wrap(page)
    
    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped browser."""
        return getattr(self._browser, name)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._browser.__exit__(exc_type, exc_val, exc_tb)


@contextmanager
def get_browser(headless: bool | None = None, slow_mo: float | None = None):
    """Recommended way to get a Playwright browser instance in Vibe Automation Framework.

    There are three running modes:
    1. during local development, we can get a local browser instance
    2. in managed execution environment, the browser instance are provided by Orby. This is
       activated via the presence of CONNECTION_URL.
    Returns a wrapped browser that automatically wraps pages with VibePage functionality
    when new_page() is called, eliminating the need for manual wrap() calls.
    """
    with sync_playwright() as p:
        connection_url = os.environ.get('CONNECTION_URL')
        if connection_url:
            # Connect to existing browser instance via CDP
            browser = p.chromium.connect_over_cdp(connection_url)
        else:
            # Launch a new browser instance
            browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        
        try:
            yield WrappedBrowser(browser)
        finally:
            browser.close()


def wrap(page: PlaywrightPage) -> VibePage:
    if isinstance(page, VibePage):
        # already wrapped
        return page

    vibe_page = VibePage.create(page)
    return vibe_page
