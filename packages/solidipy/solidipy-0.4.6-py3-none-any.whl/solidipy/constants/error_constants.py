"""
Module for dictionary mapping of standard errors.
"""

from typing import Dict


BAD_REQUEST: dict[str, str] = {
    "error": "Bad Request",
    "message": "The server would not process the request due to a client error."
}

UNAUTHORIZED: dict[str, str] = {
    "error": "Unauthorized",
    "message": "Authentication is required and has failed or has not yet been provided."
}

FORBIDDEN: dict[str, str] = {
    "error": "Forbidden",
    "message": "You do not have permission to access the requested resource."
}

NOT_FOUND: dict[str, str] = {
    "error": "Not Found",
    "message": "The requested resource could not be found on the server."
}

METHOD_NOT_ALLOWED: dict[str, str] = {
    "error": "Method Not Allowed",
    "message": "The HTTP method used is not allowed for the requested resource."
}

REQUEST_TIMEOUT: dict[str, str] = {
    "error": "Request Timeout",
    "message": "The server timed out waiting for the request."
}

CONFLICT: dict[str, str] = {
    "error": "Conflict",
    "message": "The request could not be completed due to a conflict with the current state of the resource."
}

PAYLOAD_TOO_LARGE: dict[str, str] = {
    "error": "Payload Too Large",
    "message": "The request payload is larger than the server is willing or able to process."
}

UNSUPPORTED_MEDIA_TYPE: dict[str, str] = {
    "error": "Unsupported Media Type",
    "message": "The request media type is not supported by the server."
}

I_AM_A_TEAPOT: dict[str, str] = {
    "error": "I'm a teapot",
    "message": "The server refuses to brew coffee because it is, permanently, a teapot."
}

UPGRADE_REQUIRED: dict[str, str] = {
    "error": "Upgrade Required",
    "message": "The client must switch to a different protocol, such as TLS/1.3, to proceed."
}

TOO_MANY_REQUESTS: dict[str, str] = {
    "error": "Too Many Requests",
    "message": "The client has sent too many requests in a given amount of time."
}

REQUEST_HEADER_FIELDS_TOO_LARGE: dict[str, str] = {
    "error": "Request Header Fields Too Large",
    "message": "The server is unable to process the request due to large request header fields."
}

INTERNAL_SERVER_ERROR: dict[str, str] = {
    "error": "Internal Server Error",
    "message": "The server encountered an unexpected condition that prevented it from fulfilling the request."
}

BAD_GATEWAY: dict[str, str] = {
    "error": "Bad Gateway",
    "message": "The server received an invalid response from the upstream server."
}

SERVICE_UNAVAILABLE: dict[str, str] = {
    "error": "Service Unavailable",
    "message": "The server is currently unavailable, typically due to maintenance or overloading."
}

GATEWAY_TIMEOUT: dict[str, str] = {
    "error": "Gateway Timeout",
    "message": "The server did not receive a timely response from the upstream server or application."
}

UNKNOWN_ERROR: dict[str, str] = {
    "error": "Unknown Error",
    "message": "An error occurred."
}

NOT_IMPLEMENTED: dict[str, str] = {
    "error": "Not Implemented",
    "message": "This feature is not implemented"
}


http_error_mapping: Dict[int, dict] = {
    0: UNKNOWN_ERROR,
    400: BAD_REQUEST,
    401: UNAUTHORIZED,
    403: FORBIDDEN,
    404: NOT_FOUND,
    405: METHOD_NOT_ALLOWED,
    408: REQUEST_TIMEOUT,
    409: CONFLICT,
    413: PAYLOAD_TOO_LARGE,
    415: UNSUPPORTED_MEDIA_TYPE,
    418: I_AM_A_TEAPOT,
    426: UPGRADE_REQUIRED,
    429: TOO_MANY_REQUESTS,
    431: REQUEST_HEADER_FIELDS_TOO_LARGE,
    500: INTERNAL_SERVER_ERROR,
    501: NOT_IMPLEMENTED,
    502: BAD_GATEWAY,
    503: SERVICE_UNAVAILABLE,
    504: GATEWAY_TIMEOUT,
}
"""
Mapping of all default HTTP errors with their corresponding messages.
"""
