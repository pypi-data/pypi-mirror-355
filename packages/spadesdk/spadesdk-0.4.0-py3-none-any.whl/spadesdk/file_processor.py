import abc
import dataclasses
from enum import Enum

from spadesdk.user import User

try:
    from pandera.io import from_frictionless_schema

    PANDERA_PRESENT = True
except ImportError:
    PANDERA_PRESENT = False


@dataclasses.dataclass
class File:
    """
    Dataclass representing a Spade file.
    """

    name: str
    format: str
    system_params: dict | None = None
    schema: dict | None = None


@dataclasses.dataclass
class FileUpload:
    """
    Dataclass representing the result of a file upload.
    """

    class Result(Enum):
        SUCCESS = "success"
        WARNING = "warning"
        FAILED = "failed"

    file: File
    result: Result
    rows: int | None = None
    error_message: str | None = None
    output: dict | None = None


class FileProcessor(metaclass=abc.ABCMeta):
    """
    FileProcessor processes a Spade file using the process method.
    """

    @classmethod
    @abc.abstractmethod
    def process(
        cls, file: File, filename: str, data, user_params: dict | None, user: User, *args, **kwargs
    ) -> FileUpload:
        """
        Process a file using the file processor.

        :param file: File to process and its system parameters
        :param filename: Name of the file uploaded
        :param data: Data of the file uploaded
        :param user_params: User parameters - provided by the user when uploading the file
        """

    @staticmethod
    def validate(file: File, dataframe):
        """
        Validate the file data against the file schema.

        :param file: File to validate
        :param dataframe: DataFrame containing the file data
        """

        if not PANDERA_PRESENT:
            raise ImportError("Pandera is not installed. Please install spadesdk[pandera].")

        schema = from_frictionless_schema(file.schema)
        return schema.validate(dataframe, lazy=True)
