# /solidipy/exceptions/__init__.py

""" Exceptions init """
from importlib.util import find_spec

from solidipy.exceptions.exception_handler import ExceptionHandler
from solidipy.exceptions.exception_values import EXCEPTION_TUPLE, MASTER_EXCEPTION_TUPLE

if find_spec("sqlalchemy") is not None:
	from solidipy.exceptions.exception_values import SA_EXCEPTION_TUPLE
