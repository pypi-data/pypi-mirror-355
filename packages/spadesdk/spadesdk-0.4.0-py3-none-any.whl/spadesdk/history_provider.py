import abc
import typing

from spadesdk.executor import Process, RunResult


class HistoryProvider(metaclass=abc.ABCMeta):
    """
    HistoryProvider can provide a history of process runs from an external service.
    """

    @classmethod
    @abc.abstractmethod
    def get_runs(cls, process: Process, request, *args, **kwargs) -> typing.Iterable["RunResult"]:
        """
        Get the history of a process.

        :param process: Process to get the history of
        :param request: Django request
        :param args: Additional arguments
        :param kwargs: Additional keyword arguments

        :return: Iterable of RunResult
        """
