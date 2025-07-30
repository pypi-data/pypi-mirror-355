# validation/validation.py

""" Module for validation helpers. """

import inspect
from functools import wraps
from importlib.util import find_spec


PYDANTIC_AVAILABLE: bool = find_spec("pydantic") is not None
FLASK_AVAILABLE: bool = find_spec("flask") is not None

if PYDANTIC_AVAILABLE:
	from typing import Any, Callable, Optional, Type, TypeVar, Union

	from pydantic import BaseModel, ValidationError, model_validator
	from pydantic_core import PydanticCustomError

	wrapped_func = TypeVar("wrapped_func", bound=Callable[..., Any])
	""" TypeVar used for a wrapped function. """


	class CustomValidationError(Exception):
		"""
		Custom error class used to handle Pydantic validation errors that are
		outside the scope of the library's functionality.
		"""

		def __init__(
			self,
			error_type: str,
			msg: str,
			loc: Optional[tuple] = None,
			user_input: Optional[Any] = None,
			error_code: Optional[int] = None,
		):
			"""
			CustomValidationError initialization method.

			:param error_type: The type of error that occurred.
			:param msg: The message associated with the error.
			:param loc: The field of distress.
			:param user_input: The user input that caused the error.
			"""

			self.error: dict = {
				"type": error_type,
				"msg": msg,
			}

			if loc is not None:
				self.error["loc"] = loc

			if user_input is not None:
				self.error["input"] = user_input

			if error_code is not None:
				self.error["response_code"] = error_code

		def errors(self):
			"""
			Method that mirrors the Pydantic.ValidationError.errors() method.
			:return: A list containing the error dictionary.
			"""

			return [self.error]


	class ValidationErrorHandler:
		"""
		Houses methods to parse Pydantic validation errors into formatted dictionaries.
		"""
		validation_error_types = Union[ValidationError, PydanticCustomError, CustomValidationError]
		""" Type hint for all valid Pydantic validation error types. """

		def __init__(self, validation_exception: validation_error_types):
			"""
			Initialization method.

			:param validation_exception: Dictionary representation of a Pydantic validation error.
			"""

			self.error: dict = self.__parse_error(validation_exception)

		def __parse_error(self, validation_exception: validation_error_types) -> dict:
			"""
			Pydantic validation error handler function. Deconstructs Pydantic
			Validation errors into error dictionaries.

			:param validation_exception: A Pydantic validation error.
			:return: A dictionary containing the error type and error message.
			"""

			# Get the list of errors
			error_list: list = validation_exception.errors()
			# Extract the first error from the list of errors.
			validation_error: dict = error_list[0]
			# Extract the error type.
			error_type: str = validation_error.get("type")
			# Extract the error field of distress, user input, & error message
			# from the error or None if the location is not present in the validation error.
			field_of_distress: Optional[str] = self.__unpack_location(validation_error.get("loc"))
			# If a field is missing, there will be no user input, so substitute a
			# None value to show that no value was provided for the field of distress.
			user_input: str = validation_error.get("input", "") if error_type != "missing" else None

			response_code: int = validation_error.get("response_code")

			error_response_dict: dict = {
				"Type": error_type.replace("_", " "),
				"Message": validation_error.get("msg", ""),
				"User Input": user_input
			}

			if field_of_distress:
				error_response_dict["Field of Distress"] = field_of_distress

			if response_code is not None:
				error_response_dict["Response Code"] = int(response_code)
			return error_response_dict

		@classmethod
		def __unpack_location(cls, location: Optional[tuple]) -> Optional[str]:
			"""
			Unpacks the location tuple into a string.  Reading from left to right,
			it will unpack the tuple into a string that looks like:
			('type', 0, 'name') -> type[0][name]

			:param location: Tuple containing the location of the error.
			:return: String containing the location of the error or None if the location isn't specified.
			"""

			# If the location tuple is empty, the error occurred on behalf of an erroneously empty payload.
			if location is None:
				return location

			unpacked_location: str = ""
			for attribute in location:
				unpacked_location = (
					attribute if not unpacked_location else unpacked_location + f"[{attribute}]"
				)

			return unpacked_location

	def validate_model(
		payload: dict, model: Type[BaseModel]
	) -> Union[BaseModel, dict]:
		"""
		Validate a dictionary against a Pydantic model.

		:param payload: The dictionary to validate.
		:param model: The Pydantic model to validate the dictionary against.
		"""

		# Ensure that the payload is a dictionary and the validation model is an instance of a Pydantic BaseModel.
		try:
			if not isinstance(payload, dict):
				raise TypeError(
					"'Payload' parameter supplied to the 'validate_model' function must be a dictionary."
				)
			if not isinstance(model, type) or not issubclass(model, BaseModel):
				raise TypeError(
					"'model' parameter supplied to the 'validate_model' function must be a Pydantic BaseModel."
				)

		except TypeError as exc:
			exception_dict: dict = solidipy_exception_handler.get_exception_log(exc)
			return exception_dict

		# Attempt to validate the payload against the validation model.
		try:
			validated_object: BaseModel = model(**payload)

		except (ValidationError, PydanticCustomError, CustomValidationError) as validation_exception:
			# Handle the validation error and return the error dictionary.
			validation_error_handler: ValidationErrorHandler = ValidationErrorHandler(validation_exception)
			return validation_error_handler.error

		# Return the validated object.
		return validated_object

	if FLASK_AVAILABLE:
		from flask import request
		from json import JSONDecodeError

		from solidipy.exceptions.exception_handler import solidipy_exception_handler
		from solidipy.exceptions.exception_values import MASTER_EXCEPTION_TUPLE
		from solidipy.utilities.dict_utilities import normalize_keys


		class NoRequestBody(BaseModel):
			""" Pydantic request model for a request with no body. """

			@model_validator(mode="before")
			def validate_empty_request_body(cls, request_payload: dict) -> dict:
				"""
				Pydantic model validator to ensure that the request body is empty.

				:param request_payload:
				:return:
				"""

				if bool(request_payload):
					raise CustomValidationError(
						"Unexpected request data",
						"Empty JSON payload expected.",
						("Request body",),
						user_input=request_payload,
						error_code=400
					)

				return request_payload


		def validate_request_headers(
			validation_model: Type[BaseModel]
		) -> wrapped_func:
			"""
			This is a wrapped function to be used as a decorator on functions
    		decorated as a Flask blueprint to validate incoming request headers.

			:param validation_model: Dataclass to validate the request headers.
			:return: The wrapped function.
			"""

			def inspect_request_headers(func: wrapped_func) -> wrapped_func:
				"""
				This is a wrapped function to be returned by the decorator.

				:param func: The wrapped function.
				:return: The wrapped function.
				"""

				@wraps(func)
				def wrapped(**kwargs) -> Union[BaseModel, tuple[dict, int]]:
					"""
					A wrapped function that houses request header validation logic.
					:return: Tuple containing a dictionary representation of the
					response body and an integer representing the response code.

					1. Because any HTTP request that reaches this point will have
					request headers, extract them and cast them to a dictionary.
					2. Normalize all dictionary keys to lower case.
					3. Validate the headers against the validation model & log them.
						3e. If an exception is caught, extract the first error in
						the list. Pass the extracted error to the
						"ValidationErrorHandler" and return the error dict with
						the assigned response code.
					5. If the 'request_headers' is an expected parameter in the
					decorated function, append the object to the kwargs and pass
					them to the decorated function, or next decorator in the chain.
					"""

					try:
						deserialized_headers: dict = dict(request.headers)
						normalized_headers: dict = normalize_keys(deserialized_headers)
						validated_headers: BaseModel = validation_model(**normalized_headers)

					except (ValidationError, PydanticCustomError, CustomValidationError) as validation_exception:
						validation_error: dict = ValidationErrorHandler(validation_exception).error
						error_code: int = validation_error.get("Response Code", 400)
						return validation_error, error_code

					if "request_headers" in inspect.signature(func).parameters:
						kwargs["request_headers"] = validated_headers
					return func(**kwargs)

				return wrapped

			return inspect_request_headers


		def validate_request_body(
			validation_model: Type[BaseModel] = NoRequestBody,
		) -> wrapped_func:
			"""
			This is a wrapped function to be used as a decorator on functions
    		decorated as a Flask blueprint to validate incoming request bodies.

			:param validation_model: Dataclass to validate the request payload against.
			If one isn't supplied, it's assumed that this endpoint shouldn't have data
			included in the request body, and default to a 'NoRequestBody' validation model.
			:return: The wrapped function.
			"""

			def inspect_request_payload(func: wrapped_func) -> wrapped_func:
				"""
				This is a wrapped function to be returned by the decorator.

				:param func: The wrapped function.
				:return: The wrapped function.
				"""

				@wraps(func)
				def wrapped(**kwargs) -> Union[BaseModel, tuple[dict, int]]:
					"""
					A wrapped function that houses request body validation logic.
					:return: Tuple containing a dictionary representation of the
					response body and an integer representing the response code.

					1. Attempt to deserialize the request body into a dictionary.
						1e. Raise a JSONDecodeError if the request body cannot be cast
							to a dictionary.
					2. Normalize all request dictionary keys to lower case.
					3. Attempt to validate the request body against the validation
						model.
					4. If the 'request_body' is an expected parameter in decorated the
						function, append them to the kwargs to be passed.
						4e. If an exception is caught, supply it to the validation error
							handler and return the error dict in a tuple with a 400
							response code.
					5. Pass the kwargs object to the decorated function, or next
						decorator in the chain.
					"""

					try:
						deserialized_request_body: dict = request.json
						if not isinstance(deserialized_request_body, dict):
							raise JSONDecodeError(
								"Malformed request body", f"{deserialized_request_body}", 0
							)

					except MASTER_EXCEPTION_TUPLE as exc:
						solidipy_exception_handler.get_exception_log(exc)
						return {"error": "Malformed request body"}, 400

					normalized_request_body: dict = normalize_keys(deserialized_request_body)

					try:
						validated_request_object = validation_model(**normalized_request_body)

					except (ValidationError, PydanticCustomError, CustomValidationError) as validation_exception:
						validation_error: dict = ValidationErrorHandler(validation_exception).error
						error_code: int = validation_error.get("response_code", 400)
						return validation_error, error_code

					if "request_body" in inspect.signature(func).parameters:
						kwargs["request_body"] = validated_request_object
					return func(**kwargs)

				return wrapped

			return inspect_request_payload
