from contextlib import contextmanager
from playwright.sync_api import sync_playwright, Page as PlaywrightPage
from .page import Page as VibePage


@contextmanager
def get_browser(headless: bool | None = None, slow_mo: float | None = None):
    """Recommended way to get a Playwright browser instance in Vibe Automation Framework.

    There are three running mode:
    1. during local development, we can get a local browser instance
    2. in managed execution environment, the browser instance are provided by Orby. This is
       activated via the presence of VIBE_EXECUTION_ID.

    TODO: request browser instance in the managed execution environment
    """
    with sync_playwright() as p:
        with p.chromium.launch(headless=headless, slow_mo=slow_mo) as browser:
            yield browser


def wrap(page: PlaywrightPage) -> VibePage:
    if isinstance(page, VibePage):
        # already wrapped
        return page

    vibe_page = VibePage.create(page)
    return vibe_page
