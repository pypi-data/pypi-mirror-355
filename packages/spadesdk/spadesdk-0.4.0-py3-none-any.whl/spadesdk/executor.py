import abc
import dataclasses
from datetime import datetime
from enum import Enum

from spadesdk.user import User


@dataclasses.dataclass
class Process:
    """
    Dataclass representing a Spade process.
    """

    code: str
    system_params: dict | None = None


@dataclasses.dataclass
class RunResult:
    """
    Base class for the result of a process run.
    """

    class Status(Enum):
        NEW = "new"
        RUNNING = "running"
        FINISHED = "finished"
        FAILED = "failed"

    class Result(Enum):
        SUCCESS = "success"
        WARNING = "warning"
        FAILED = "failed"

    process: Process
    status: Status
    result: Result | None = None
    error_message: str | None = None
    output: dict | None = None
    created_at: datetime | None = None
    user_id: int | None = None


class Executor(metaclass=abc.ABCMeta):
    """
    Executor executes a Spade process using the run method.
    It can either directly run some code or call an external service,
    form example trigger an Airflow DAG.
    """

    @classmethod
    @abc.abstractmethod
    def run(cls, process: Process, user_params: dict, user: User, *args, **kwargs) -> RunResult:
        """
        Execute a process using the executor.

        :param process: Process to run and its system parameters
        :param user_params: User parameters - provided by the user when running the process
        :param user_id: The id of the user running the process

        :return: RunResult
        """
