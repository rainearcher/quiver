"""Command handlers. Importing this package populates the registry."""

from loom_mcp.commands import read, write  # noqa: F401  (import for side effects)
from loom_mcp.registry import COMMANDS, GROUPS, Command

__all__ = ["COMMANDS", "GROUPS", "Command"]
