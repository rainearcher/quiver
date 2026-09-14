"""The 30 write commands.

Importing this module registers every write command. The handlers live in
:mod:`write_video`, :mod:`write_social` (comments, tasks, reactions) and
:mod:`write_library` (folders, Watch Later, tags).

Every handler validates its IDs first, then short-circuits on ``--dry-run``
before any request reaches Loom.
"""

from loom_mcp.commands import (  # noqa: F401  (imported for side effects)
    write_library,
    write_social,
    write_video,
)
from loom_mcp.commands.support import dry, ok, parse_settings

__all__ = [
    "dry",
    "ok",
    "parse_settings",
    "write_library",
    "write_social",
    "write_video",
]
