"""Helpers shared by the read and write handlers."""

import json

from loom_mcp import render
from loom_mcp.errors import LoomCLIError
from loom_mcp.output import Result


async def paged(fetch, key: str, limit: int, drain: bool) -> list:
    """Drain a cursor-paginated endpoint, stopping at ``limit`` unless ``drain``."""
    items: list = []
    cursor = None
    while drain or len(items) < limit:
        size = 50 if drain else min(50, limit - len(items))
        batch = await fetch(limit=size, cursor=cursor)
        items.extend(batch[key])
        if not batch["hasNextPage"]:
            break
        # Stop if the server claims another page but hands back the same (or no)
        # cursor: without this, --all would spin forever on a misbehaving API.
        if batch["endCursor"] is None or batch["endCursor"] == cursor:
            break
        cursor = batch["endCursor"]
    return items if drain else items[:limit]


def dry(ns, operation: str, **params) -> Result | None:
    """Return a preview Result when --dry-run is set, else None."""
    if not getattr(ns, "dry_run", False):
        return None
    lines = [f"[dry-run] {operation}"]
    lines.extend(f"  {k} = {v!r}" for k, v in params.items())
    return Result(
        data={"dry_run": True, "operation": operation, "params": params},
        text="\n".join(lines),
    )


def ok(payload) -> Result:
    """Default write rendering: the raw payload as indented JSON."""
    return Result(data=payload, text=render.pretty_json(payload))


def parse_settings(pairs: list[str]) -> dict:
    """Turn repeated ``--set KEY=VALUE`` into a dict, JSON-decoding each value."""
    settings: dict = {}
    for item in pairs:
        key, sep, raw = item.partition("=")
        key = key.strip()
        if not sep or not key:
            raise LoomCLIError(
                f"Invalid --set value: {item!r} (expected KEY=VALUE)", kind="usage"
            )
        try:
            settings[key] = json.loads(raw)
        except json.JSONDecodeError:
            settings[key] = raw
    return settings
