"""Command-line utilities for NcatBot."""

from ncatbot.cli.utils.cli_exceptions import CLIExit
from ncatbot.cli.utils.constants import PYPI_SOURCE, PLUGIN_INDEX_URL
from ncatbot.cli.utils.pip_tool import install_pip_dependencies
from ncatbot.cli.utils.plugin_utils import (
    download_plugin_file,
    get_plugin_index,
    get_plugin_versions,
)

__all__ = [
    # Constants
    "PYPI_SOURCE",
    "PLUGIN_INDEX_URL",
    # Plugin utilities
    "get_plugin_index",
    "download_plugin_file",
    "get_plugin_versions",
    # Package management
    "install_pip_dependencies",
    # CLI exceptions
    "CLIExit",
]
