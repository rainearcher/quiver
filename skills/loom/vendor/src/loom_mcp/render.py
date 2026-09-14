"""Pure payload -> text formatters.

Every function here is side-effect free: no network, no filesystem, no printing.
Output strings are byte-identical to the MCP server they replace so existing
saved files keep their shape.
"""

import json
from typing import Any


def fmt_duration(seconds: Any) -> str:
    """Format a playable duration as ``1h 2m 3s`` (hours omitted when zero)."""
    m, s = divmod(int(seconds or 0), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s"


def _stamp(value: Any, key: str) -> str:
    return f" @{value[key]}s" if value.get(key) is not None else ""


def pretty_json(payload: Any) -> str:
    return json.dumps(payload, indent=2)


# --- collections -----------------------------------------------------------


def videos_table(videos: list[dict], label: str = "videos") -> str:
    lines = [f"{v['id']}  {v['name']}" for v in videos]
    return f"Found {len(videos)} {label}:\n\n" + "\n".join(lines)


def folders_table(folders: list[dict], visibility: bool = True) -> str:
    if visibility:
        lines = [
            f"{f['id']}  {f['name']}  ({f.get('visibility', 'unknown')})"
            for f in folders
        ]
    else:
        lines = [f"{f['id']}  {f['name']}" for f in folders]
    return f"Found {len(folders)} folders:\n\n" + "\n".join(lines)


def spaces_table(spaces: list[dict]) -> str:
    lines = []
    for s in spaces:
        primary = " (primary)" if s.get("is_primary") else ""
        privacy = s.get("privacy") or "unknown"
        lines.append(f"{s['id']}  {s['name']}  [{privacy}]{primary}")
    return f"Found {len(spaces)} spaces:\n\n" + "\n".join(lines)


# --- per-video detail ------------------------------------------------------


def comment_lines(comments: list[dict], markdown: bool = False) -> list[str]:
    """Flatten threaded comments.

    ``markdown=False`` produces the saved-file shape (``  └─ `` replies);
    ``markdown=True`` produces the nested-bullet shape used in details.md.
    """
    bullet = "- " if markdown else ""
    reply_prefix = "  - " if markdown else "  └─ "
    lines = []
    for c in comments:
        ts = _stamp(c, "time_stamp")
        lines.append(f"{bullet}[{c['user_name']}{ts}] {c['content']}")
        for r in c.get("children_comments") or []:
            lines.append(f"{reply_prefix}[{r['user_name']}] {r['content']}")
    return lines


def comments_text(comments: list[dict]) -> str:
    return "\n".join(comment_lines(comments))


def task_lines(tasks: list[dict]) -> list[str]:
    lines = []
    for t in tasks:
        owner = (t.get("owner") or {}).get("display_name", "Unassigned")
        ts = _stamp(t, "time_stamp")
        status = "resolved" if t.get("resolved_at") else "open"
        lines.append(f"[{status}] [{owner}{ts}] {t['content']}")
    return lines


def tasks_text(tasks: list[dict]) -> str:
    return "\n".join(task_lines(tasks))


def reactions_text(reactions: list[dict]) -> str:
    lines = []
    for r in reactions:
        user = (r.get("user") or {}).get("display_name") or r.get(
            "anon_user_name", "Anonymous"
        )
        emoji = r.get("extended_reaction") or r.get("reaction", "")
        ts = _stamp(r, "time")
        lines.append(f"[{user}{ts}] {emoji}")
    return "\n".join(lines)


def comment_reactions_text(reactions: list[dict]) -> str:
    lines = []
    for r in reactions:
        emoji = r.get("extendedReaction", "")
        user = r.get("userName", "Unknown")
        lines.append(f"[{user}] {emoji}")
    return "\n".join(lines)


def backlinks_text(backlinks: list[dict]) -> str:
    lines = []
    for b in backlinks:
        source = b.get("source", "unknown")
        title = b.get("title", "Untitled")
        link = b.get("sourceLink", "")
        lines.append(f"[{source}] {title} — {link}")
    return "\n".join(lines)


def takeaways_text(takeaways: list[str]) -> str:
    return "\n".join(f"- {t}" for t in takeaways)


def confluence_links(pages: list[dict]) -> str:
    return "\n".join(
        f"- [{p.get('title', 'Untitled')}]({p.get('url', '')})" for p in pages
    )


def frequent_reactions_text(reactions: list[str]) -> str:
    return "Your frequent reactions: " + ", ".join(reactions)


# --- the aggregate view ----------------------------------------------------


def video_details_markdown(
    video: dict,
    chapters: dict | None,
    summary: dict | None,
    transcript: str | None,
    tasks: list[dict],
    comments: list[dict],
) -> str:
    """Assemble the combined markdown emitted by ``loom video details``."""
    parts = [f"# {video.get('name', 'Unknown')}\n"]

    parts.append(f"**Duration:** {fmt_duration(video.get('playable_duration'))}")
    parts.append(f"**Created:** {video.get('createdAt', 'Unknown')}")
    parts.append(
        f"**Owner:** {(video.get('owner') or {}).get('display_name', 'Unknown')}"
    )
    parts.append(f"**Views:** {(video.get('views') or {}).get('total', 0)}")
    parts.append("")

    if chapters and chapters.get("content"):
        parts.append("## Chapters\n")
        parts.append(chapters["content"])
        parts.append("")

    if summary and summary.get("autoDescription"):
        parts.append("## AI Summary\n")
        parts.append(summary["autoDescription"])
        parts.append("")

    if transcript:
        parts.append("## Transcript\n")
        parts.append(transcript)
        parts.append("")

    if tasks:
        parts.append("## Action Items\n")
        parts.extend(f"- {line}" for line in task_lines(tasks))
        parts.append("")

    if comments:
        parts.append("## Comments\n")
        parts.extend(comment_lines(comments, markdown=True))

    return "\n".join(parts)
