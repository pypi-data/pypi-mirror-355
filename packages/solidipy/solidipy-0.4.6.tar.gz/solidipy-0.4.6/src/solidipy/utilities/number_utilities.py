# /utility/number_utilities.py

""" Module for utility functions related to integer and floating point operations. """

from math import ceil, floor


def get_rounded_quotient(dividend: int, divisor: int, round_up: bool = True) -> int:
	"""
	Utility function for getting a quotient that is rounded.

	:param dividend: The numeric value to divide.
	:param divisor: The numeric value to divide the dividend by.
	:param round_up: Flag that indicates whether to round up or down.
	:return: Rounded quotient to the nearest whole number, or None if the operation fails.
	"""

	if not isinstance(dividend, int) or not isinstance(divisor, int):
		raise ValueError("Both inputs must be integers.")
	if divisor == 0:
		raise ZeroDivisionError("Divisor cannot be 0.")
	rounded_quotient: int = ceil(dividend / divisor) if round_up else floor(dividend / divisor)
	return rounded_quotient
