"""
Http utilities.
"""

from importlib.util import find_spec

if PYDANTIC_AVAILABLE := find_spec("pydantic") is not None:
    from solidipy.utilities.http.http_response import HttpResponse
    from solidipy.utilities.http.http_error import HttpError

if FLASK_AVAILABLE := find_spec("flask") is not None:
    from solidipy.utilities.http.http_response import FlaskResponseType
