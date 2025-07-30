"""
Base HTTP error response class.
"""

from importlib.util import find_spec

if PYDANTIC_AVAILABLE := find_spec("pydantic") is not None:
    from typing import Optional
    from pydantic import model_validator, Field

    from solidipy.constants.error_constants import http_error_mapping, UNKNOWN_ERROR
    from solidipy.utilities.http.http_response import HttpResponse


    class HttpError(HttpResponse):
        """
        Base class for all HTTP(s)-based API errors.
        """

        error: Optional[str] = Field(default=None)
        """
        The type of error returned to the client application.
        """

        message: Optional[str] = Field(default=None)
        """
        A message describing the error returned to the client.
        """

        @model_validator(mode="after")
        def set_defaults_based_on_status_code(self) -> "HttpError":
            """
            Validator to set `error` and `message` based on `status_code` if not provided.

            :return: The updated HttpApiError instance with defaults applied.
            """

            current_error: dict = http_error_mapping.get(
                self.status_code, UNKNOWN_ERROR
            )

            if self.error is None:
                self.error = current_error["error"]

            if self.message is None:
                self.message = current_error["message"]

            return self
