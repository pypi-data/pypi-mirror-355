import json
from pathlib import Path

import nbformat
from nbformat import NotebookNode

from ssb_pubmd.constants import METADATA_FILE
from ssb_pubmd.constants import ContentType
from ssb_pubmd.request_handler import RequestHandler
from ssb_pubmd.request_handler import Response


class MarkdownSyncer:
    """This class syncs a content file to a CMS (Content Management System).

    The CMS must have an endpoint that satisfies the following constraints:

    -   It must accept a post request with fields *_id*, *displayName* and *markdown*.
    -   The response body must have a key *_id* whose value should be
        a unique string identifier of the content.

    Creating and updating content is handled in the following way:

    -   On the first request, an empty string is sent as *_id*.
    -   If the request succeeds, the value of *_id* (in the response) is stored in a JSON file
        (created in the same directory as the markdown/notebook file).
    -   On subsequent requests, the stored value is sent as *_id*.
    """

    ID_KEY = "_id"

    def __init__(
        self,
        post_url: str,
        request_handler: RequestHandler,
        metadata_file: Path = METADATA_FILE,
    ) -> None:
        """Creates a markdown syncer instance that connects to the CMS through the post url."""
        self._post_url: str = post_url
        self._request_handler: RequestHandler = request_handler
        self._content_file_path: Path = Path()
        self._content_file_type: ContentType = ContentType.MARKDOWN
        self._metadata_file_path: Path = metadata_file

    @property
    def content_file_path(self) -> Path:
        """Returns the path of the content file."""
        return self._content_file_path

    @content_file_path.setter
    def content_file_path(self, path: Path) -> None:
        """Sets the path of the content file."""
        if not path.is_file():
            raise FileNotFoundError(f"The file {path} does not exist.")

        ext = path.suffix.lower()
        for t in ContentType:
            if ext == t.value:
                self._content_file_type = t
                break
        else:
            allowed_extensions = [t.value for t in ContentType]
            sep = ", "
            raise ValueError(
                f"The file {path} has extension {ext}, but should be one of: {sep.join(allowed_extensions)}."
            )

        self._content_file_path = path

    @property
    def basename(self) -> str:
        """The name of the content file without extension."""
        return self._content_file_path.stem

    @property
    def display_name(self) -> str:
        """Generate a display name for the content."""
        return self.basename.replace("_", " ").title()

    @property
    def metadata_file_path(self) -> Path:
        """The path of the metadata file."""
        return self._metadata_file_path

    @property
    def metadata_key(self) -> str:
        """The key that the content metadata will be stored under in the metadata file."""
        return str(self._content_file_path.absolute())

    def _save_content_id(self, content_id: str) -> None:
        """Saves the content id to the metadata file."""
        with open(self._metadata_file_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

        data[self.metadata_key] = {
            self.ID_KEY: content_id,
        }

        with open(self._metadata_file_path, "w") as f:
            json.dump(data, f, indent=4)

    def _get_content_id(self) -> str:
        """Fetches the content id from the metadata file if it exists, otherwise an empty string."""
        with open(self._metadata_file_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

        metadata: dict[str, str] = data.get(self.metadata_key, {})

        content_id = metadata.get(self.ID_KEY, "")

        return content_id

    def _read_notebook(self) -> NotebookNode:
        """Reads the notebook file and returns its content."""
        return nbformat.read(self._content_file_path, as_version=nbformat.NO_CONVERT)  # type: ignore

    def _get_content_from_notebook_file(self) -> str:
        """Extracts all markdown cells from the notebook and returns it as a merged string."""
        notebook = self._read_notebook()

        markdown_cells = []
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                markdown_cells.append(cell.source)

        markdown_content = "\n\n".join(markdown_cells)

        return markdown_content

    def _get_content_from_markdown_file(self) -> str:
        """Returns the content of a markdown file."""
        with open(self._content_file_path) as file:
            markdown_content = file.read()
        return markdown_content

    def _get_content(self) -> str:
        content = ""
        match self._content_file_type:
            case ContentType.MARKDOWN:
                content = self._get_content_from_markdown_file()
            case ContentType.NOTEBOOK:
                content = self._get_content_from_notebook_file()
        return content

    def _request_data(self) -> dict[str, str]:
        """Prepares the request data to be sent to the CMS endpoint."""
        return {
            "_id": self._get_content_id(),
            "displayName": self.display_name,
            "markdown": self._get_content(),
        }

    def sync_content(self) -> Response:
        """Sends the request to the CMS endpoint and returns the content id from the response."""
        response = self._request_handler.send_request(
            url=self._post_url, data=self._request_data()
        )

        if response.status_code != 200:
            raise ValueError(
                f"Request to the CMS failed with status code {response.status_code}."
            )
        if response.body is None:
            raise ValueError("Response body from CMS could not be parsed.")
        if self.ID_KEY not in response.body:
            raise ValueError(
                f"Response from the CMS does not contain the expected key '{self.ID_KEY}'."
            )
        result = response.body[self.ID_KEY]
        if not isinstance(result, str):
            raise ValueError(
                f"Response from the CMS does not contain a valid content id: {result}"
            )
        content_id: str = result
        self._save_content_id(content_id)

        return response
