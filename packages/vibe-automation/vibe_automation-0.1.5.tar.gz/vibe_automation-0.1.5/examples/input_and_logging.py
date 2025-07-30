import logging
from pydantic import BaseModel

from va import workflow


class Contact(BaseModel):
    name: str
    phone: str


@workflow("Workflow input example")
def main(input: Contact, logger: logging.Logger):
    """ "
    During local development, we would use the input provided in the main guard (Contact with name John).
    When the script get executed in our managed environment, the `workflow` wrapper would replace the
    first argument with the execution input, after performing some type validation if the input has type
    hint from Pydantic.

    The first argument must have the name "input" to activate this behavior. Otherwise, we would print out
    a warning message and keep the argument unchanged.

    In addition, we also provide a managed logger instance that would automatically collect all logs
    to the execution service for easy debugging. All the logs are associated with the corresponding execution.
    """
    logger.info("Contact name: %s", input.name)
    logger.info("Contact phone: %s", input.phone)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(Contact(name="John", phone="123-456-7890"), logger=logging.getLogger(__name__))
