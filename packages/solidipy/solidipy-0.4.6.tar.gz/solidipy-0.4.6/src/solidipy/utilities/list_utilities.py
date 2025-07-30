# /utilities/list_utilities.py

""" Module for utility functions related to list operations. """

from typing import Any, List


def is_every_list_item_unique(list_to_evaluate: List[Any]) -> bool:
	"""
	Utility function to determine if a list contains only unique items.

	:param list_to_evaluate: List to test.
	:return: Boolean indicating if every item in the list is unique.
	"""

	seen: set[Any] = set(list_to_evaluate)
	return len(seen) == len(list_to_evaluate)


def list_contents_are_identical_without_order(
	list_one: List[Any], list_two: List[Any]
) -> bool:
	"""
	Utility function for determining if two lists contain the same items, regardless of order.

	:param list_one: The first list to compare.
	:param list_two: The second list to compare against.
	:return: Boolean indicating if the list contents match.
	"""

	return (set(list_one) == set(list_two)) and (len(list_one) == len(list_two))


def serialize_list(items: List[str]) -> str:
	"""
	Utility function that serializes a list of strings into a single string.

	:param items: List of strings.
	:returns: Single serialized string containing list.
	"""

	return ",".join(items)


def deserialize_list(serialized: str) -> List[str]:
	"""
	Utility function that deserializes a list of strings from a single string.

	:param serialized: Serialized list of strings.
	:returns: Deserialized list.
	"""

	return serialized.split(",")
