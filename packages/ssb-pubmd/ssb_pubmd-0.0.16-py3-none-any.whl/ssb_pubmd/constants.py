from enum import Enum

from platformdirs import user_cache_path
from platformdirs import user_config_path
from platformdirs import user_data_path

APP_NAME = "pubmd"

METADATA_FILE = user_data_path(APP_NAME, ensure_exists=True) / "metadata.json"
CACHE_FILE = user_cache_path(APP_NAME, ensure_exists=True) / "cache.json"
CONFIG_FILE = user_config_path(APP_NAME, ensure_exists=True) / "config.json"

CACHE_FILE.touch()
CONFIG_FILE.touch()
METADATA_FILE.touch()


class ContentType(Enum):
    """Allowed content types."""

    MARKDOWN = ".md"
    NOTEBOOK = ".ipynb"
