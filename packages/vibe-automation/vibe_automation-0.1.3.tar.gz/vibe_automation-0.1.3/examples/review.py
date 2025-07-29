import logging

from va import step, review, workflow, ReviewStatus
from va.playwright import get_browser


@workflow("Example workflow")
def main():
    with get_browser(headless=False, slow_mo=1000) as browser:
        page = browser.new_page()

        with step("navigate to the form"):
            page.goto("https://forms.gle/pV8CD8cAjgZPWcmV6")

        with step("fill the form"):
            page.get_by_label("What is the item you would like to order?").fill(
                "T-shirt"
            )
            page.get_by_label("Your name").fill("<NAME>")

        with step("submit the form"):
            r = review("final-review", "Check if the form is correct")
            if r.status != ReviewStatus.READY:
                print("exiting execution since review is not ready")
                return
            page.get_by_text("Submit").click()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
