"""
Base http-response class.
"""

from __future__ import annotations

from importlib.util import find_spec

if FLASK_AVAILABLE := find_spec("flask") is not None:

    from typing import Any, Callable, Dict, Iterable, Union
    from flask import Response

    FlaskResponseType = Union[
        Response,  # Full Flask response object
        int,  # Status code only
        str,  # Response body as string
        bytes,  # Response body as bytes
        None,  # Empty response with default status code
        Dict,  # JSON-like response
        tuple,  # One of several combinations of response body, headers, and status code.
        Callable[[], Union[Response, Iterable[bytes]]],  # Streaming response
    ]
    """
    FlaskResponseType:
    A type representing all possible response formats recognized by Flask route handlers.
    Only intended to
    """

    if PYDANTIC_AVAILABLE := find_spec("pydantic") is not None:
        from pydantic import BaseModel, ConfigDict, Field


        class HttpResponse(BaseModel):
            """
            Base class for all API responses success or Error.
            """

            model_config = ConfigDict(extra="forbid")
            """
            Pydantic object that restricts the response
            payload to contain only the applicable fields.
            """

            status_code: int = Field(default=0, ge=0, le=504)
            """
            The HTTP status code of the response.
            """

            headers: Dict[str, str] = Field(default_factory=dict)
            """
            Optional dictionary mapping of HTTP headers for the response.
            """

            def get_response(self) -> FlaskResponseType:
                """
                Generates a status code and or response tuple for Flask, optionally
                including headers.

                :return: Returns some combination of a status code, response body, and
                response headers.
                """

                response_tuple: tuple[int] = (self.status_code,)  # Start with the status code

                # Create a dictionary of all fields except 'status_code' and 'headers'.
                response_body: Dict[str, Any] = self.model_dump(
                    exclude={"status_code", "headers"}
                )

                if response_body:
                    if self.headers:
                        return response_body, self.status_code, self.headers
                    return response_body, self.status_code

                if self.headers:
                    return "", self.status_code, self.headers

                return "", self.status_code
