# logging_utility/base_logger.py

""" Solidipy Logger. """

import asyncio
import json
import logging
from asyncio import AbstractEventLoop
from datetime import date
from logging import FileHandler, Formatter, Logger, StreamHandler
from os import path
from pathlib import Path
from typing import AnyStr, Callable, Optional, Type, Union


class BaseLogger:
    """ BaseLogger class implementation. """

    def __init__(
        self,
        logger: Optional[Logger] = logging.getLogger("log"),
        logs_dir_path: Union[str, AnyStr, Path, None] = None,
        format_str: str = "[%(levelname)s %(asctime)s]:: %(message)s",
    ):
        """
        Initializer for the BaseLogger.

        :param logger: Logger instance to be set.
        :param logs_dir_path: Path to the directory where the log file should be initialized and stored.
        """

        self.logger = None
        self.format = format_str.strip()

        if not self.set_logger(logger):
            raise ValueError("Logger failed to initialize.")

        self.__remove_existing_handlers()
        self.set_format(format_str=self.format)

        if logs_dir_path is not None and not self.set_log_file(str(logs_dir_path)):
            raise ValueError(
                "Log file path supplied to `BaseLogger` at init must be a valid, absolute path ending in a directory."
            )

    def set_logger(
        self,
        new_logger: Union[Logger, Type[Logger], None] = None,
    ) -> bool:
        """
        Method used to set configurations on the BaseLogger.

        :param new_logger: Logger instance to be set.
        :return: Flag indicating if the logger has been set.
        """

        if new_logger is not None:
            self.logger = new_logger
            # set the logging level to debug so all messages are
            # logged and, if enabled, able to be written to a file.
            self.logger.setLevel(logging.DEBUG)
        return self.logger is not None

    def set_log_file(self, log_file: Optional[str]) -> bool:
        """
        Public method used to reset or remove the filepath & file handler of
        the logger after init.

        :param log_file: Absolute path to the log file dir.
        If None, the FileHandler will be removed.
        :return: Boolean indicating the success of the operation.
        """

        if log_file:
            log_file = self.__validate_log_file_path(log_file)
            if not log_file:
                return False

        for handler in self.logger.handlers:
            if isinstance(handler, FileHandler):
                handler.close()
                self.logger.removeHandler(handler)
                break

        if log_file is not None:
            self.__set_log_handler(log_file)

        return True

    def set_format(self, format_str: str) -> bool:
        """
        Method used to set the formatting of the logger.
        :param format_str: The format to prepend logs with.
        :return Flag indicating operation success.
        """

        try:
            # Default to raw message if format string is blank
            formatter: Formatter = (
                Formatter('%(message)s') if not format_str
                else Formatter(format_str, datefmt='%m/%d %H:%M:%S')
            )

            # Validate the format string by formatting a fake LogRecord
            record = self.logger.makeRecord(
                name=self.logger.name,
                level=logging.INFO,
                fn="test.py",
                lno=1,
                msg="test message",
                args=None,
                exc_info=None
            )
            formatter.format(record)

            handler: StreamHandler = StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.format: str = format_str

        except (ValueError, AttributeError, TypeError) as exc:
            self.log_error(
                f"{type(exc).__name__}! Could not set logger format: {format_str}"
            )
            return False

        return True

    def get_logger_info(self) -> dict:
        """
        Method used to retrieve the logger information.

        :return: Dictionary containing the logger information.
        """

        log_obj: dict = {"name": self.logger.name}
        return log_obj

    def log_message(self, reflection: str, message: str) -> Optional[bool]:
        """
        Flexible method used to granular-ly set the logging priority before
            logging the incoming message.

        :param reflection: Reflection of the logging priority for the logging
            message.
        :param message: Message to be logged.
        :return: Flag indicating operation success.
        """

        logger_method: Optional[Callable] = getattr(
            self.logger, reflection.lower(), None
        )
        if logger_method is None:
            return False
        logger_method(message)
        return True

    def log_info(self, message: str) -> bool:
        """
        Method used for logging a friendly information-level message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = self.log_message("info", message)
        return log_success

    def log_json(self, json_dict: dict, tag: str = "", indent: int = 4) -> bool:
        """
        Method used for logging a json-structure with an optional message.

        :param json_dict: Dictionary representation of a JSON payload.
        :param tag: A message to be logged ahead of the payload.
        :param indent: The number of spaces to apply to the tabs of the JSON
        formatting.  Defaults to a normal tab size of 4.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = self.log_message(
            "info", f"{tag}{json.dumps(json_dict, indent=indent)}"
        )
        return log_success

    def log_debug(self, message: str) -> bool:
        """
        Method used for logging a friendly information-level message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = self.log_message("debug", message)
        return log_success

    def log_warning(self, message: str) -> bool:
        """
        Method used for logging a warning message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = self.log_message("warning", message)
        return log_success

    def log_error(self, message: str) -> bool:
        """
        Method used for logging an error-level message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = self.log_message("error", message)
        return log_success

    def log_exception(self, message: str) -> bool:
        """
        Method used for logging an exception-level message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = self.log_message("critical", message)
        return log_success

    async def log_async_debug(self, message: str) -> bool:
        """
        Method used for logging an asynchronous debug-level message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = await self.log_async_message("debug", message)
        return log_success

    async def log_async_info(self, message: str) -> bool:
        """
        Method used for logging an asynchronous friendly information-level message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = await self.log_async_message("info", message)
        return log_success

    async def log_async_json(self, json_dict: dict, tag: str = "", indent: int = 4) -> bool:
        """
        Method used for asynchronously logging a json-structure with an optional message.

        :param json_dict: Dictionary representation of a JSON payload.
        :param tag: The message to be logged ahead of the payload.
        :param indent: The number of spaces to apply to the tabs of the JSON
        formatting.  Defaults to a normal tab size of 4.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = await self.log_async_message(
            "info", f"{tag}{json.dumps(json_dict, indent=indent)}"
        )
        return log_success

    async def log_async_warning(self, message: str) -> bool:
        """
        Method used for logging an asynchronous warning message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = await self.log_async_message("warning", message)
        return log_success

    async def log_async_error(self, message: str) -> bool:
        """
        Method used for logging an asynchronous error-level message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = await self.log_async_message("error", message)
        return log_success

    async def log_async_exception(self, message: str) -> bool:
        """
        Method used for logging an asynchronous exception-level message.

        :param message: The message to be logged.
        :return: Flag indicating the success of the message logging.
        """

        log_success: bool = await self.log_async_message("critical", message)
        return log_success

    async def log_async_message(self, reflection: str, message: str) -> bool:
        """
        Flexible method used to granular-ly set the logging priority before
            asynchronously logging the incoming message.

        :param reflection: Reflection of the logging priority for the logging
            message.
        :param message: Message to be logged.
        :return: Flag indicating operation success.
        """

        logger_method: Optional[Callable[..., None]] = getattr(self.logger, reflection.lower(), None)
        if logger_method is None:
            return False
        loop: AbstractEventLoop = asyncio.get_event_loop()
        await loop.run_in_executor(None, logger_method, message)
        return True

    def __remove_existing_handlers(self):
        """
        Method used to clean up and remove existing handlers (used in log
        formatting) from the logger.

        NOTE: `self.logger.handlers.clear()` is not being used because it
        doesn't call cleanup or close methods on the individual handler objects.
        """

        for handler in self.logger.handlers:
            # Close the handler if it has a close method
            if hasattr(handler, "close"):
                handler.close()
            # Remove the handler from the logger
            self.logger.removeHandler(handler)

    def __set_log_handler(self, log_directory_path: str):
        """
        Method used to set the file handler of the logger.

        :param log_directory_path: The path to the directory where the log file should be initialized and stored.
        """

        current_file_path: str = f"{log_directory_path}/{self.logger.name}__{date.today():%Y-%m-%d}.log"

        file_handler: FileHandler = FileHandler(current_file_path)
        file_handler.setFormatter(self.logger.handlers[0].formatter)
        self.logger.addHandler(file_handler)

    @classmethod
    def __validate_log_file_path(cls, log_file: str) -> str:
        """
        Method used to validate the log file path.

        :param log_file: Absolute path to the log file dir.
        :return: String containing the validated log file path or an empty string if it's invalid.
        """

        if not path.abspath(log_file) or not path.isdir(log_file):
            return ""
        return log_file

    # Alias normal logging methods for concise syntax im business logic.
    info = log_info
    json = log_json
    debug = log_debug
    warning = log_warning
    error = log_error
    exception = log_exception
    async_log = log_async_info
    async_json = log_async_json
    async_debug = log_async_debug
    async_warning = log_async_warning
    async_error = log_async_error
    async_exception = log_async_exception


solidipy_logger = BaseLogger(
    logger=logging.getLogger(name="solidipy"), format_str="%(levelname)s %(message)s"
)
"""
Universal logging object for logging operations across the package.
Not intended for use outside of the package.
"""
