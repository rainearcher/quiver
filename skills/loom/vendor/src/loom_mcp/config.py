"""Project-root discovery, ``.env`` loading, and Loom client construction."""

import json
import os
from pathlib import Path

from loom_mcp.client import LoomClient
from loom_mcp.errors import LoomCLIError

AUTH_HELP_URL = "https://github.com/karbassi/loom-mcp#authentication"


def find_project_root() -> Path | None:
    """Walk up from this file to find the directory containing pyproject.toml."""
    d = Path(__file__).resolve().parent
    while d != d.parent:
        if (d / "pyproject.toml").exists():
            return d
        d = d.parent
    return None


# In a local dev checkout (loom-api/mcp-server/), the project root's parent
# contains .env and auth.json.  When installed via uvx, find_project_root()
# returns None and these paths are skipped gracefully.
PROJECT_ROOT = find_project_root()


def load_dotenv(project_root: Path | None = PROJECT_ROOT) -> None:
    """Populate os.environ from ``<project_root>/../.env`` without overriding."""
    if project_root is None:
        return
    env_path = project_root.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


load_dotenv()


def normalize_cookie(cookie: str) -> str:
    """Auto-prepend the ``connect.sid=`` prefix when the raw value is given."""
    if cookie and not cookie.startswith("connect.sid="):
        return f"connect.sid={cookie}"
    return cookie


def resolve_auth(
    cookie_arg: str | None = None,
    auth_file_arg: str | None = None,
    timeout: float = 30.0,
) -> LoomClient:
    """Build a LoomClient from --cookie/--auth-file, falling back to the env."""
    cookie = normalize_cookie(cookie_arg or os.environ.get("LOOM_COOKIE", ""))
    if cookie:
        return LoomClient(cookies=cookie, timeout=timeout)

    auth_file = auth_file_arg or os.environ.get("LOOM_AUTH_FILE")
    if not auth_file and PROJECT_ROOT is not None:
        auth_file = str(PROJECT_ROOT.parent / "auth.json")
    if not auth_file:
        raise LoomCLIError(
            "Set LOOM_COOKIE or LOOM_AUTH_FILE, or pass --cookie/--auth-file. "
            f"See {AUTH_HELP_URL}",
            kind="auth",
        )

    try:
        return LoomClient(auth_file=auth_file, timeout=timeout)
    except FileNotFoundError:
        raise LoomCLIError(
            f"Auth file not found: {auth_file}. See {AUTH_HELP_URL}", kind="auth"
        ) from None
    except (json.JSONDecodeError, KeyError, TypeError):
        raise LoomCLIError(
            f"Auth file {auth_file} is not a valid Playwright storage-state file. "
            f"See {AUTH_HELP_URL}",
            kind="auth",
        ) from None
