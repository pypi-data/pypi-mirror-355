from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

from playwright.sync_api import BrowserContext
from playwright.sync_api import sync_playwright

from ssb_pubmd.request_handler import Response


class CreateContextMethod(Enum):
    """The method used to create the browser context.

    Can be either from a file containing the context data,
        or from a login popup window.
    """

    FROM_FILE = "from_file"
    FROM_LOGIN = "from_login"


class BrowserRequestHandler:
    """This class is used to create a logged in browser context from which to send requests."""

    def __init__(self, context_file_path: Path, login_url: str) -> None:
        """Initializes an empty browser context object."""
        self._context_file_path: Path = context_file_path
        self._login_url: str = login_url
        self._context: BrowserContext | None = None

    @contextmanager
    def new_context(
        self, method: CreateContextMethod = CreateContextMethod.FROM_FILE
    ) -> Iterator[BrowserContext]:
        """Wrapper around playwright's context manager.

        The default is to create a new context from a file.
        If `from_file` is  set False, a new context is created through a browser popup with user login,
            and the context is saved to a file.
        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            match method:
                case CreateContextMethod.FROM_FILE:
                    self._context = browser.new_context(
                        storage_state=self._context_file_path
                    )
                case CreateContextMethod.FROM_LOGIN:
                    self._context = browser.new_context()
                    login_page = self._context.new_page()
                    login_page.goto(self._login_url)
                    login_page.wait_for_event("close", timeout=0)
                    self._context.storage_state(path=self._context_file_path)
            yield self._context
            self._context.close()
            browser.close()

    def send_request(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> Response:
        """Sends a request to the specified url, optionally with headers and data, within the browser context."""
        if self._context is None:
            raise ValueError("Browser context has not been created.")

        api_response = self._context.request.post(
            url,
            data=data,
        )

        try:
            body = api_response.json()
            body = dict(body)
        except Exception:
            body = {}

        response = Response(
            status_code=api_response.status,
            body=body,
        )

        return response
