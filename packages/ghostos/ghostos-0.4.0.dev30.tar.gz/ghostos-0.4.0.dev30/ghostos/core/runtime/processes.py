from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field
from ghostos_common.entity import EntityMeta
from contextlib import contextmanager
from ghostos_common.helpers import uuid

__all__ = [
    'GoProcess',
    'GoProcesses',
]


class GoProcess(BaseModel):
    process_id: str = Field(
        description="""
Unique process id for the agent session. Session shall only have one process a time.
Stop the process will stop all the tasks that belongs to it.
""",
    )

    matrix_id: str = Field(
        description="session id in which the process belongs",
    )

    @classmethod
    def new(
            cls, *,
            matrix_id: str,
            process_id: Optional[str] = None,
    ) -> "GoProcess":
        process_id = process_id if process_id else uuid()
        return GoProcess(
            matrix_id=matrix_id,
            process_id=process_id,
        )


class GoProcesses(ABC):
    """
    repository to save or load process
    """

    @abstractmethod
    def get_process(self, matrix_id: str) -> Optional[GoProcess]:
        """
        get process by id
        :param matrix_id: belongs to the matrix
        """
        pass

    @abstractmethod
    def save_process(self, process: GoProcess) -> None:
        """
        save process
        :param process:
        :return:
        """
        pass

    @contextmanager
    def transaction(self):
        """
        transaction to process io
        do nothing as default.
        """
        yield
