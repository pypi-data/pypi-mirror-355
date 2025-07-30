from typing import Optional, Callable
from playwright.sync_api import Locator
import functools


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
        if isinstance(other, PromptBasedLocator):
            raise ValueError(
                "Cannot use two get_by_prompt locators together with | operator"
            )
        return PromptBasedLocator(self.page, self.prompt, other)

    def __or__(self, other) -> "PromptBasedLocator":
        """Support for the | operator (page.get_by_prompt('...') | page.get_by_text('Save'))"""
        if isinstance(other, PromptBasedLocator):
            raise ValueError(
                "Cannot use two get_by_prompt locators together with | operator"
            )
        else:
            # For regular Locator objects, we need to create a new PromptBasedLocator
            # where 'other' becomes the fallback for 'self'
            # But since we can't extract prompt from regular locator, we keep self as primary
            return PromptBasedLocator(self.page, self.prompt, other)

    def _get_prompt_locator(self) -> Locator:
        """Get the prompt-based locator, raising an exception if it can't be found."""
        locator = self.page._get_locator_by_prompt(self.prompt)
        if locator is None:
            raise Exception(f"Could not locate element with prompt: {self.prompt}")
        return locator

    def _wrap_method(self, method_name: str, method: Callable) -> Callable:
        """Wrap a method to try fallback locator first, then prompt-based locator on exception."""

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            # If we have a fallback locator, try it first
            if self.fallback_locator:
                try:
                    fallback_method = getattr(self.fallback_locator, method_name)
                    return fallback_method(*args, **kwargs)
                except Exception:
                    # If fallback fails, continue to prompt-based locator
                    pass

            # Try prompt-based locator
            prompt_locator = self._get_prompt_locator()
            prompt_method = getattr(prompt_locator, method_name)
            return prompt_method(*args, **kwargs)

        return wrapper

    def __getattribute__(self, name):
        # Get our own attributes first
        if name in (
            "page",
            "prompt",
            "fallback_locator",
            "_get_prompt_locator",
            "_wrap_method",
            "__ror__",
            "__or__",
            "__init__",
            "__class__",
        ):
            return object.__getattribute__(self, name)

        # For all other attributes, check if it's a method that should be wrapped
        # First try to get the attribute from a fallback locator or create a prompt locator
        if self.fallback_locator:
            try:
                # Try fallback locator first to see if the attribute exists
                attr = getattr(self.fallback_locator, name)
            except AttributeError:
                # If attribute doesn't exist on fallback, try prompt locator
                try:
                    prompt_locator = self._get_prompt_locator()
                    attr = getattr(prompt_locator, name)
                except AttributeError:
                    # If both fail, raise the original AttributeError
                    raise AttributeError(
                        f"'{self.__class__.__name__}' object has no attribute '{name}'"
                    )
        else:
            # No fallback locator, use prompt locator directly
            prompt_locator = self._get_prompt_locator()
            attr = getattr(prompt_locator, name)

        # If it's a callable (method), wrap it with exception handling
        if callable(attr):
            return self._wrap_method(name, attr)
        else:
            # For non-callable attributes, return the attribute directly from target locator
            # but still with fallback logic in case of exceptions
            if self.fallback_locator:
                try:
                    return getattr(self.fallback_locator, name)
                except AttributeError:
                    pass

            # Fall back to prompt-based locator for attributes
            prompt_locator = self._get_prompt_locator()
            return getattr(prompt_locator, name)
