# /utilities/exception/exception_handler.py

""" Exception handler class definition. """

import json
from logging import Logger
from typing import NoReturn, Union

from solidipy.exceptions.exception_values import GENERIC_ERROR_DICT, MASTER_EXCEPTION_DICT
from solidipy.logging_utility.base_logger import BaseLogger, solidipy_logger as sl


class ExceptionHandler:
	""" Base class for handling exceptions. """

	def __init__(
		self, singleton_logger: Union[Logger, BaseLogger, None] = None
	):
		"""
		Initializer for the ExceptionHandler class.

		:param singleton_logger: Instance of a BaseLogger class.
		"""

		self.logger = singleton_logger

	def get_exception_log(self, exception) -> dict:
		"""
		Method for assembling and logging_utility exception information.

		:param exception: Exception object that was raised.
		:return: Formatted dictionary log of exception that occurred.
		"""

		exception_dict: dict = self.__get_exception_dict(exception)

		if self.logger is not None and hasattr(self.logger, "log_exception"):
			self.__log_exception(exception_dict)

		return exception_dict

	@classmethod
	def __get_exception_dict(cls, exception) -> dict:
		"""
		Method for retrieving the exception dictionary for a given exception.

		:param exception: Exception that occurred.
		:return: The requested dictionary of mapped exception values or a
			generic error dictionary if the key is not found.
		"""

		queried_dict: dict = MASTER_EXCEPTION_DICT.get(
			exception.__class__.__name__, GENERIC_ERROR_DICT
		)
		exception_args: tuple = exception.args

		if queried_dict != GENERIC_ERROR_DICT and len(exception_args) > 0:

			if isinstance(exception_args[0], str) and len(exception_args[0]):
				queried_dict["Message"] = exception_args[0]

		if queried_dict.get("Message", '') == '':
			queried_dict.pop("Message", None)

		return queried_dict

	def __log_exception(self, exception_dict: dict) -> NoReturn:
		"""
		Method that formats a log and then logging_utility it.

		:param exception_dict: Exception dictionary to be logged.
		"""

		log: str = self.__format_exception_log(exception_dict)
		self.logger.log_exception(log)  # noqa

	@classmethod
	def __format_exception_log(cls, exception_dict: dict) -> str:
		"""
		Method for formatting an exception log.

		:param exception_dict: Exception dictionary to be logged.
		:return: Formatted exception log.
		"""

		log: str = (
			f"{json.dumps(exception_dict, indent=4)}"
		)
		max_length = max(len(line) for line in log.split('\n'))
		exception_message: str = " An exception occurred "
		message_length = len(exception_message)
		divider_length = max_length + 2
		left_divider_length = (divider_length - message_length) // 2
		right_divider_length = divider_length - message_length - left_divider_length
		top_divider: str = "=" * left_divider_length + exception_message + "=" * right_divider_length
		bottom_divider: str = "=" * divider_length
		return f"\n\n{top_divider}\n{log}\n{bottom_divider}\n\n"


solidipy_exception_handler: ExceptionHandler = ExceptionHandler(sl)
"""
Universal exception handling object for operations across the package.
Not intended for use outside of the package.
"""
