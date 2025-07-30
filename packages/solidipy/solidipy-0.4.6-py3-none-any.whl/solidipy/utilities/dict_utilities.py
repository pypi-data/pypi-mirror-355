# /utilities/dict_utilities.py

""" Module for utility functions related to dictionary operations. """


def normalize_keys(input_dict: dict) -> dict:
	"""
	Utility function to normalize all string keys in a dictionary to lowercase.
	:param input_dict: Input dictionary.
	:return: Dictionary with all string keys cast to lowercase.
	"""

	# Ensure that the input is a dictionary.
	if not isinstance(input_dict, dict):
		raise ValueError("Input must be a dictionary.")

	# Return an empty dictionary if the input is empty.
	if not input_dict:
		return input_dict

	# Return a dictionary with all string keys cast to lowercase.
	return {
		key.lower() if isinstance(key, str)
		else key: value for key, value in input_dict.items()
	}
