from enum import Enum
from typing import Any

from pydantic import BaseModel


class ExecutionModel(BaseModel):
    id: str
    input: Any


class ReviewStatus(Enum):
    PENDING = 1
    READY = 2


class ReviewModal(BaseModel):
    id: str
    type: str
    instruction: str
    artifacts: list[Any] | None
    status: ReviewStatus
    data: Any
