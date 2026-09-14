"""The single output chokepoint: Result, emit(), and save_payload().

Every byte the CLI writes to stdout or stderr goes through :func:`emit`.
No other module writes to the process streams.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Result:
    """What a command handler returns.

    ``data``      the raw payload printed under ``--json``.
    ``text``      the human rendering printed by default (may be empty).
    ``note``      an out-of-band remark ("No transcript available…") -> stderr.
    ``save_name`` canonical filename used by ``--save-dir`` (e.g. transcript.txt).
    ``save_key``  subdirectory under ``--save-dir`` (always the video id).
    ``saved``     extra paths already written by the handler.
    """

    data: Any = None
    text: str = ""
    note: str | None = None
    save_name: str | None = None
    save_key: str | None = None
    saved: tuple[Path, ...] = field(default_factory=tuple)


def save_payload(
    save_dir: str | None, key: str, filename: str, content: str
) -> Path | None:
    """Write ``content`` to ``<save_dir>/<key>/<filename>``; no-op when either is empty."""
    if not save_dir or not content:
        return None
    target_dir = Path(save_dir).expanduser().resolve() / key
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def _stderr(line: str) -> None:
    sys.stderr.write(f"{line}\n")


def emit(result: Result, args) -> None:
    """Render a Result according to the global flags on ``args``."""
    as_json = getattr(args, "json", False)
    payload = json.dumps(result.data, indent=2, default=str) if as_json else result.text

    saved = list(result.saved)
    save_dir = getattr(args, "save_dir", None)
    if save_dir and result.save_name and result.save_key:
        path = save_payload(save_dir, result.save_key, result.save_name, result.text)
        if path is not None:
            saved.append(path)

    quiet = getattr(args, "quiet", False)
    destination = getattr(args, "output", None)
    if destination and destination != "-":
        out_path = Path(destination).expanduser()
        out_path.write_text(_terminated(payload), encoding="utf-8")
        if not quiet:
            _stderr(f"[Wrote {out_path}]")
    else:
        sys.stdout.write(_terminated(payload))

    if quiet:
        return
    if result.note:
        _stderr(result.note)
    for path in saved:
        _stderr(f"[Saved to {path}]")


def error(message: str) -> None:
    """Write a single ``loom: <message>`` line to stderr."""
    _stderr(f"loom: {message}")


def _terminated(payload: str) -> str:
    if not payload:
        return ""
    return payload if payload.endswith("\n") else payload + "\n"
