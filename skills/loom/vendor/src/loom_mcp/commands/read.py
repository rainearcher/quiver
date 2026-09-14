"""The 30 read commands.

Importing this module registers every read command. The handlers live in
:mod:`read_video` (the 19 video commands) and :mod:`read_library` (comments,
reactions, folders, spaces, Watch Later, tags and users).
"""

from loom_mcp.commands import read_library, read_video  # noqa: F401  (side effects)
from loom_mcp.commands.support import paged

__all__ = ["paged", "read_library", "read_video"]
