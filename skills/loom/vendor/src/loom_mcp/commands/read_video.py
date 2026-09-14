"""Read commands for the ``video`` group (19 commands)."""

import asyncio

from loom_mcp import render
from loom_mcp.client import LoomClient
from loom_mcp.commands import args as A
from loom_mcp.commands.support import paged
from loom_mcp.errors import LoomCLIError, check_id
from loom_mcp.output import Result, save_payload
from loom_mcp.registry import command


# --- video: listing and search --------------------------------------------


@command(
    "video",
    "list",
    "List your Loom videos, sorted by most recent.\n\n"
    "Returns video IDs and names. Use 'loom video get' for metadata on a specific\n"
    "video, or 'loom video details' for everything including transcript and comments.",
    configure=A.paging(noun="videos"),
)
async def video_list(client: LoomClient, ns) -> Result:
    videos = await paged(client.list_videos, "videos", ns.limit, ns.all)
    return Result(data=videos, text=render.videos_table(videos))


@command(
    "video",
    "search",
    "Search Loom videos by keyword. Returns matching video IDs and names.",
    configure=A.chain(A.query, A.paging(noun="results")),
)
async def video_search(client: LoomClient, ns) -> Result:
    async def fetch(limit, cursor):
        return await client.search_videos(ns.query, limit=limit, cursor=cursor)

    videos = await paged(fetch, "videos", ns.limit, ns.all)
    if not videos:
        return Result(data=[], note=f"No videos matching '{ns.query}'")
    return Result(data=videos, text=render.videos_table(videos, "matching videos"))


# --- video: metadata -------------------------------------------------------


@command(
    "video",
    "get",
    "Get metadata for a Loom video: name, duration, owner, views, creation date.\n\n"
    "For everything including transcript, chapters, summary and comments in one\n"
    "call, use 'loom video details' instead.",
    configure=A.video_id,
)
async def video_get(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    video = await client.get_video(vid)
    if video.get("message"):
        raise LoomCLIError(
            f"Cannot access video {vid}: {video['message']}", kind="notfound"
        )
    return Result(
        data=video,
        text=render.pretty_json(video),
        save_name="metadata.json",
        save_key=vid,
    )


@command(
    "video",
    "details",
    "Get everything about a Loom video in one call.\n\n"
    "Metadata, transcript, chapters, summary, tasks and comments, rendered as\n"
    "markdown. For just the metadata use 'loom video get'.\n\n"
    "With --save-dir this also writes metadata.json, chapters.txt, summary.txt,\n"
    "transcript.txt, tasks.txt, comments.txt and details.md.",
    configure=A.video_id,
)
async def video_details(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    video = await client.get_video(vid)
    if video.get("message"):
        raise LoomCLIError(
            f"Cannot access video {vid}: {video['message']}", kind="notfound"
        )
    transcript, chapters, summary, comments, tasks = await asyncio.gather(
        client.get_transcript_text(vid),
        client.get_chapters(vid),
        client.get_summary(vid),
        client.get_comments(vid),
        client.get_tasks(vid),
    )

    save_dir = getattr(ns, "save_dir", None)
    saved = []

    def keep(filename: str, content: str) -> None:
        path = save_payload(save_dir, vid, filename, content)
        if path is not None:
            saved.append(path)

    keep("metadata.json", render.pretty_json(video))
    if chapters and chapters.get("content"):
        keep("chapters.txt", chapters["content"])
    if summary and summary.get("autoDescription"):
        keep("summary.txt", summary["autoDescription"])
    if transcript:
        keep("transcript.txt", transcript)
    if tasks:
        keep("tasks.txt", render.tasks_text(tasks))
    if comments:
        keep("comments.txt", render.comments_text(comments))

    combined = render.video_details_markdown(
        video, chapters, summary, transcript, tasks, comments
    )
    return Result(
        data={
            "video": video,
            "transcript": transcript,
            "chapters": chapters,
            "summary": summary,
            "tasks": tasks,
            "comments": comments,
        },
        text=combined,
        save_name="details.md",
        save_key=vid,
        saved=tuple(saved),
    )


# --- video: text assets ----------------------------------------------------


@command(
    "video",
    "transcript",
    "Get the full transcript of a Loom video with timestamps and speaker names.\n\n"
    "Plain text, one line per phrase. For per-cue start/end timing in WebVTT,\n"
    "use 'loom video captions' instead.",
    configure=A.video_id,
)
async def video_transcript(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    text = await client.get_transcript_text(vid)
    if not text:
        return Result(note="No transcript available for this video.")
    return Result(data=text, text=text, save_name="transcript.txt", save_key=vid)


@command(
    "video",
    "captions",
    "Get WebVTT captions with start and end timestamps per cue.\n\n"
    "Ideal for precise timing analysis. For plain text with speaker names,\n"
    "use 'loom video transcript' instead.",
    configure=A.video_id,
)
async def video_captions(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    vtt = await client.get_captions(vid)
    if not vtt:
        return Result(note="No captions available for this video.")
    return Result(data=vtt, text=vtt, save_name="captions.vtt", save_key=vid)


@command(
    "video",
    "summary",
    "Get the AI-generated summary of a Loom video (1-2 concise sentences).\n\n"
    "For a detailed timestamped breakdown use 'loom video description'; for key\n"
    "highlights use 'loom video takeaways'; for chapter markers 'loom video chapters'.",
    configure=A.video_id,
)
async def video_summary(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    summary = await client.get_summary(vid)
    if not summary or not summary.get("autoDescription"):
        return Result(note="No AI summary available for this video.")
    text = summary["autoDescription"]
    return Result(data=text, text=text, save_name="summary.txt", save_key=vid)


@command(
    "video",
    "chapters",
    "Get AI-generated chapter markers with timestamps for a Loom video.\n\n"
    "Useful for navigating long videos. For a narrative summary use 'loom video summary'.",
    configure=A.video_id,
)
async def video_chapters(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    chapters = await client.get_chapters(vid)
    if not chapters or not chapters.get("content"):
        return Result(note="No chapters available for this video.")
    text = chapters["content"]
    return Result(data=text, text=text, save_name="chapters.txt", save_key=vid)


@command(
    "video",
    "takeaways",
    "Get AI-generated key takeaways from a Loom video as a bullet list.\n\n"
    "For a narrative summary use 'loom video summary'; for a detailed timestamped\n"
    "breakdown use 'loom video description'.",
    configure=A.video_id,
)
async def video_takeaways(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    takeaways = await client.get_key_takeaways(vid)
    if not takeaways:
        return Result(data=[], note="No key takeaways available for this video.")
    return Result(
        data=takeaways,
        text=render.takeaways_text(takeaways),
        save_name="takeaways.txt",
        save_key=vid,
    )


@command(
    "video",
    "description",
    "Get the AI-generated description with timestamped sections and bullet points.\n\n"
    "More detailed than 'loom video summary'.",
    configure=A.video_id,
)
async def video_description(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    desc = await client.get_description(vid)
    if not desc:
        return Result(note="No description available for this video.")
    return Result(data=desc, text=desc, save_name="description.txt", save_key=vid)


@command(
    "video",
    "tags",
    "Get tags on a Loom video.",
    configure=A.video_id,
)
async def video_tags(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    tags = await client.get_tags(vid)
    if not tags:
        return Result(data=[], note="No tags on this video.")
    return Result(data=tags, text=", ".join(tags), save_name="tags.txt", save_key=vid)


# --- video: social ---------------------------------------------------------


@command(
    "video",
    "comments",
    "Get comments on a Loom video, including threaded replies and timestamps.",
    configure=A.video_id,
)
async def video_comments(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    comments = await client.get_comments(vid)
    if not comments:
        return Result(data=[], note="No comments on this video.")
    return Result(
        data=comments,
        text=render.comments_text(comments),
        save_name="comments.txt",
        save_key=vid,
    )


@command(
    "video",
    "tasks",
    "Get AI-generated action items from a Loom video, with assignee, status and timestamp.",
    configure=A.video_id,
)
async def video_tasks(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    tasks = await client.get_tasks(vid)
    if not tasks:
        return Result(data=[], note="No tasks/action items for this video.")
    return Result(
        data=tasks,
        text=render.tasks_text(tasks),
        save_name="tasks.txt",
        save_key=vid,
    )


@command(
    "video",
    "reactions",
    "Get emoji reactions on a Loom video, including who reacted and at what timestamp.",
    configure=A.video_id,
)
async def video_reactions(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    reactions = await client.get_reactions(vid)
    if not reactions:
        return Result(data=[], note="No reactions on this video.")
    return Result(
        data=reactions,
        text=render.reactions_text(reactions),
        save_name="reactions.txt",
        save_key=vid,
    )


@command(
    "video",
    "backlinks",
    "Get external references to a Loom video — where it has been shared or embedded.",
    configure=A.video_id,
)
async def video_backlinks(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    backlinks = await client.get_backlinks(vid)
    if not backlinks:
        return Result(data=[], note="No backlinks for this video.")
    return Result(
        data=backlinks,
        text=render.backlinks_text(backlinks),
        save_name="backlinks.txt",
        save_key=vid,
    )


@command(
    "video",
    "confluence",
    "Get Confluence pages linked to a Loom video.",
    configure=A.video_id,
)
async def video_confluence(client: LoomClient, ns) -> Result:
    pages = await client.get_confluence_pages(check_id(ns.video_id, "video ID"))
    if not pages:
        return Result(data=[], note="No Confluence pages linked to this video.")
    return Result(data=pages, text=render.confluence_links(pages))


@command(
    "video",
    "meeting-notes",
    "Get the Confluence meeting notes URL linked to a Loom video.",
    configure=A.video_id,
)
async def video_meeting_notes(client: LoomClient, ns) -> Result:
    url = await client.get_meeting_notes_url(check_id(ns.video_id, "video ID"))
    if not url:
        return Result(note="No meeting notes linked to this video.")
    return Result(data=url, text=url)


@command(
    "video",
    "download-url",
    "Get a signed MP4 download URL for a Loom video.\n\n"
    "The URL is temporary and will expire. If none is available, run\n"
    "'loom video regenerate-mp4 <id>' then retry after ~30 seconds.",
    configure=A.video_id,
)
async def video_download_url(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    url = await client.get_download_url(vid)
    if not url:
        return Result(
            note=(
                "No download URL available. Run `loom video regenerate-mp4 "
                f"{vid}`, then retry after ~30 seconds."
            )
        )
    return Result(data=url, text=url)


@command(
    "video",
    "watch-time",
    "Get the last timestamp (in seconds) where you stopped watching a Loom video.",
    configure=A.video_id,
)
async def video_watch_time(client: LoomClient, ns) -> Result:
    seconds = await client.get_last_watch_time(check_id(ns.video_id, "video ID"))
    if seconds is None:
        return Result(note="No watch history for this video.")
    return Result(data=seconds, text=f"Last watched at {seconds}s")
