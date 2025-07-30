from contextlib import contextmanager

from va.automation import Automation


@contextmanager
def step(description: str):
    automation = Automation.get_instance()
    automation.execution.mark_step_executing(description)
    try:
        yield
    finally:
        automation.execution.mark_step_executed(description)
