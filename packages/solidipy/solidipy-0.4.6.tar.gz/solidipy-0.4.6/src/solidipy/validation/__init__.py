# /solidipy/validation/__init__.py

""" Validation init """

from importlib.util import find_spec

if find_spec("pydantic") is not None:
	from solidipy.validation.validation import (
		CustomValidationError,
		ValidationErrorHandler,
		validate_model
	)

	if find_spec("flask") is not None:
		from solidipy.validation.validation import (
			NoRequestBody,
			validate_request_headers,
			validate_request_body
		)
