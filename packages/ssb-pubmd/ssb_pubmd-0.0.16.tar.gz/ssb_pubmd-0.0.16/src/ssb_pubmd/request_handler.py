from dataclasses import dataclass
from typing import Any
from typing import Protocol

import requests


@dataclass
class Response:
    """The response object used in the package."""

    status_code: int
    body: dict[str, Any]


class RequestHandler(Protocol):
    """Interface for handling how a request are sent.

    Implementing classes may handle authentication, sessions, etc.
    """

    def send_request(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> Response:
        """Sends the request to the specified url, optionally with headers and data, and returns the response."""
        ...


class BasicRequestHandler:
    """Basic, unauthenticated request handler."""

    def send_request(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> Response:
        """Sends the request to the specified url without any headers."""
        response = requests.post(
            url,
            data=data,
        )

        try:
            body = response.json()
            body = dict(body)
        except Exception:
            body = {}

        return Response(
            status_code=response.status_code,
            body=body,
        )
