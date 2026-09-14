"""loom_mcp — the ``loom`` command-line client for Loom's internal GraphQL API."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mcp-loom")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    __version__ = "0.0.0"

__all__ = ["__version__"]
