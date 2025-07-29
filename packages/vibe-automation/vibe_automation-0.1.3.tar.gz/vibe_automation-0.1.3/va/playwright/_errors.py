import logging
import textwrap


log = logging.getLogger("va.playwright")


class BaseError(Exception):
    def __init__(
        self,
        error,
    ):
        self.error = error
        log.debug(f"Error occurred: {error}")

    def __str__(self):
        return f"{self.__class__.__name__}: {self.error}"


class AccessibilityTreeError(BaseError):
    def __init__(
        self,
        message=textwrap.dedent(
            """
            An error occurred while generating accessibility tree.
            The page may no longer be available due to navigation, being closed, or crashing. 
            """
        ),
    ):
        super().__init__(message)


class ElementNotFoundError(BaseError):
    def __init__(self, page_url, element_id=None):
        if element_id:
            message = f"The element with ID {element_id} could not be found on the current page anymore."
        else:
            message = "The element could not be found on the current page anymore."

        message += textwrap.dedent(
            f"""
            The element may have been removed from the page or the page may have been navigated away from.
            The current page url is: {page_url}
            """
        )

        super().__init__(message)


class PageMonitorNotInitializedError(BaseError):
    def __init__(
        self,
    ):
        message = textwrap.dedent(
            """
            The page monitor is not initialized.
            Please use the 'page.wait_for_page_ready_state()' method to wait for the page to reach a stable state.
            """
        )
        super().__init__(message)


class PageCrashError(BaseError):
    def __init__(self, page_url):
        message = textwrap.dedent(
            f"""
            One of the pages have crashed.
            The crashed page url is: {page_url}
            """
        )
        super().__init__(message)
