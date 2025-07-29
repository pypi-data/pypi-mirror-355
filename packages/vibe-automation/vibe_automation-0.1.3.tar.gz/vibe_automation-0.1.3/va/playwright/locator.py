from typing import Optional
from playwright.sync_api import Locator


class PromptBasedLocator:
    """Provides the LLM prompt-based locator when the default locator doesn't work.

    For example:

    button = page.get_by_text('Save') | page.get_by_prompt('The save button on the main form')
    button.click()

    In this case, when we call the click method, we would first try the locator from `page.get_by_text('Save')`.
    If it doesn't work, we would then use LLM to locate the element by prompt, and then perform the action.

    It can also be used independently like `page.get_by_prompt('Save button').click()`.
    """

    def __init__(self, page, prompt: str, fallback_locator: Optional[Locator] = None):
        self.page = page
        self.prompt = prompt
        self.fallback_locator = fallback_locator

    def __ror__(self, other: Locator) -> "PromptBasedLocator":
        """Support for the | operator (page.get_by_text('Save') | page.get_by_prompt('...')"""
        return PromptBasedLocator(self.page, self.prompt, other)

    def _get_locator(self, name: str) -> Locator:
        """Get the actual locator to use, trying fallback first if available."""
        if self.fallback_locator:
            try:
                # Check if fallback locator can find element
                num_elements = self.fallback_locator.count()
                if num_elements == 1 or (num_elements > 1 and name not in ('click', 'fill', 'focus', 'hover', 'pressSequentially')):
                    return self.fallback_locator
            except Exception:
                pass

        # Fall back to prompt-based locator
        locator = self.page._get_locator_by_prompt(self.prompt)
        if locator is None:
            raise Exception(f"Could not locate element with prompt: {self.prompt}")
        return locator

    def __getattribute__(self, name):
        # Get our own attributes first
        if name in (
            "page",
            "prompt",
            "fallback_locator",
            "_get_locator",
            "__ror__",
            "__init__",
            "__class__",
        ):
            return object.__getattribute__(self, name)

        # For all other attributes, delegate to the actual locator
        locator = self._get_locator(name)
        return getattr(locator, name)
