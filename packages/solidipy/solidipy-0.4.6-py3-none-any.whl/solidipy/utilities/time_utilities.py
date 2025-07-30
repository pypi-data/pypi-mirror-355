# /utilities/time_utilities.py

""" Module for utility functions related to date and time operations. """

import calendar
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Optional


def get_time_in_future(
	seconds: int = 0,
	minutes: int = 0,
	hours: int = 0,
	days: int = 0,
	weeks: int = 0
) -> datetime:
	"""
	Utility function for returning a date in the future down to the matching second.

	:param seconds: Number of seconds to push into the future.
	:param minutes: Number of minutes to push into the future.
	:param hours: Number of hours to push into the future.
	:param days: Number of days to push into the future.
	:param weeks: Number of weeks to push into the future.
	:return: Cumulative time in the future measured down to the nearest second in UTC.
	"""

	days_after: datetime = (
		datetime.utcnow() +
		timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)
	).replace(microsecond=0)

	return days_after


def is_after_today(date_and_time: datetime) -> bool:
	"""
	Utility function for telling if a given date and time is later than today.

	:param date_and_time: The date and time of interest to compare.
	:return: Flag that tells whether the param is later than today.
	"""

	if not isinstance(date_and_time, datetime):
		raise TypeError("Input must be a datetime object.")

	return date_and_time > datetime.utcnow()


def get_datetime_in_epoch(date_and_time: datetime) -> int:
	"""
	Utility function for converting a datetime object into epoch seconds.

	:param date_and_time: Date time object to be converted.
	:return: date_and_time parameter in epoch seconds.
	"""

	if not isinstance(date_and_time, datetime):
		raise TypeError("Input must be a datetime object.")

	return calendar.timegm(date_and_time.utctimetuple())


def get_iso_datestr(date_and_time: datetime) -> str:
	"""
	Utility function for converting a datetime object into a standardized ISO format.

	:param date_and_time: `datetime` object to convert.
	:return: ISO datetime string.

	- Input: 2022-01-25 22:56:00.911847
	- Output: "2022-01-25T22:56:00+00:00"
	NOTE: if a tz unaware datetime is passed, as the parameter or a non-UTC datetime
	is passed, this function will convert the datetime to UTC before output.
	"""

	if not isinstance(date_and_time, datetime):
		raise TypeError("Input must be a datetime object.")

	# If no timezone is set, assume UTC.
	if date_and_time.tzinfo is None:
		date_and_time = date_and_time.replace(tzinfo=timezone.utc)
	else:
		date_and_time = date_and_time.astimezone(timezone.utc)

	date_and_time = date_and_time.replace(microsecond=0)
	return date_and_time.isoformat()


def get_seconds_remaining_until_expiration(
	expiration_date_time: datetime,
	comparison_time: Optional[datetime] = None
) -> int:
	"""
	Utility function for determining how many seconds are left until an expiration date and time.
	If no second argument is supplied, it is assumed that the current time is the comparison time.

	:param expiration_date_time: Timestamp to use to designate the expiration.
	:param comparison_time: Optional parameter to use to compare against the expiration_date_time.
	:return: Zero if expiration_seconds have elapsed.  Otherwise, the number of remaining seconds
	will be returned.
	"""

	if not isinstance(expiration_date_time, datetime):
		raise TypeError("expiration_date_time must be a datetime object.")

	if comparison_time is not None and not isinstance(comparison_time, datetime):
		raise TypeError("comparison_time must be a datetime object if supplied.")

	# Use the timezone of the expiration_date_time if it is set.  Otherwise, assume UTC.
	standardized_timezone: tzinfo = (
		expiration_date_time.tzinfo
		if expiration_date_time.tzinfo is not None else
		timezone.utc
	)

	# If the expiration_date_time is not timezone-aware, set it to the standardized timezone.
	expiration_date_time: datetime = (
		expiration_date_time.replace(tzinfo=standardized_timezone)
		if expiration_date_time.tzinfo is None else
		expiration_date_time
	)

	# Determine if the comparison exists.  If it doesn't, set it to the current time.
	comparison_time = (
		datetime.now(standardized_timezone)
		if comparison_time is None else
		comparison_time.replace(tzinfo=standardized_timezone)
	)

	time_difference: float = (
		(expiration_date_time - comparison_time).total_seconds()
		if expiration_date_time > comparison_time else 0
	)

	return max(0, int(time_difference))
