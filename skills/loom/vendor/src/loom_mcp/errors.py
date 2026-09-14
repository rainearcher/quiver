"""Error types, ID validation, and the exception -> exit-code mapping."""

import re
from enum import IntEnum

import httpx

from loom_mcp.client import LoomAPIError

_ID_RE = re.compile(r"\A[a-zA-Z0-9_.\-]{1,200}\Z")


class ExitCode(IntEnum):
    """Process exit codes. ``OK`` covers empty-but-successful reads."""

    OK = 0
    ERROR = 1
    USAGE = 2
    AUTH = 3
    NOT_FOUND = 4
    NETWORK = 5
    INTERRUPT = 130


#: Error ``kind`` -> exit code. Kinds are shared with ``LoomAPIError.kind``.
KIND_EXIT_CODES: dict[str, ExitCode] = {
    "usage": ExitCode.USAGE,
    "auth": ExitCode.AUTH,
    "notfound": ExitCode.NOT_FOUND,
    "network": ExitCode.NETWORK,
    "ratelimit": ExitCode.NETWORK,
    "api": ExitCode.ERROR,
    "error": ExitCode.ERROR,
}


class LoomCLIError(Exception):
    """A user-facing CLI failure: one clean stderr line, no traceback."""

    def __init__(self, message: str, kind: str = "error"):
        super().__init__(message)
        self.kind = kind


def exit_code_for(exc: BaseException) -> int:
    """Map an exception to the process exit code it should produce."""
    if isinstance(exc, (LoomCLIError, LoomAPIError)):
        return int(KIND_EXIT_CODES.get(getattr(exc, "kind", "error"), ExitCode.ERROR))
    if isinstance(exc, httpx.HTTPError):
        # Covers TimeoutException, ConnectError, HTTPStatusError and friends.
        return int(ExitCode.NETWORK)
    if isinstance(exc, KeyboardInterrupt):
        return int(ExitCode.INTERRUPT)
    return int(ExitCode.ERROR)


def message_for(exc: BaseException) -> str:
    """Render an exception as a single human-readable line."""
    if isinstance(exc, httpx.HTTPStatusError):
        return (
            f"Loom returned HTTP {exc.response.status_code} for {exc.request.url.host}."
        )
    if isinstance(exc, httpx.TimeoutException):
        return "Timed out talking to Loom."
    if isinstance(exc, httpx.HTTPError):
        return f"Network error talking to Loom: {exc}"
    text = str(exc).strip()
    return text or exc.__class__.__name__


def check_id(value: str, label: str = "ID") -> str:
    """Validate a single resource ID against the Loom ID charset."""
    if not _ID_RE.fullmatch(value):
        raise LoomCLIError(f"Invalid {label}: {value!r}", kind="usage")
    return value


def check_ids(values: list[str], label: str = "ID") -> list[str]:
    """Validate every ID in a list, returning it unchanged."""
    for v in values:
        check_id(v, label)
    return values
