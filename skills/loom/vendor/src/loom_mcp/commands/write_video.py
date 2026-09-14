"""Write commands for the ``video`` group (12 commands)."""

from loom_mcp.client import LoomClient
from loom_mcp.commands import args as A
from loom_mcp.commands.support import dry, ok, parse_settings
from loom_mcp.errors import LoomCLIError, check_id, check_ids
from loom_mcp.output import Result
from loom_mcp.registry import command


# --- video -----------------------------------------------------------------


def _rename_args(p):
    A.video_id(p)
    p.add_argument("--name", required=True, metavar="TEXT", help="The new video name")


@command(
    "video",
    "rename",
    "Rename a Loom video. Overwrites the existing name.",
    configure=_rename_args,
    write=True,
)
async def video_rename(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(ns, "update_video_name", video_id=vid, name=ns.name):
        return preview
    result = await client.update_video_name(vid, ns.name)
    name = result.get("name", ns.name)
    return Result(data=result, text=f"Renamed to: {name}")


def _description_args(p):
    A.video_id(p)
    p.add_argument(
        "--description",
        required=True,
        metavar="TEXT",
        help="The new video description ('-' reads stdin)",
    )


@command(
    "video",
    "set-description",
    "Update the description of a Loom video. Overwrites the existing description.",
    configure=_description_args,
    write=True,
)
async def video_set_description(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    description = A.read_text(ns.description)
    if preview := dry(
        ns, "update_video_description", video_id=vid, description=description
    ):
        return preview
    return ok(await client.update_video_description(vid, description))


def _settings_args(p):
    A.video_id(p)
    p.add_argument(
        "--set",
        dest="settings",
        action="append",
        required=True,
        metavar="KEY=VALUE",
        help=(
            "Setting to update, repeatable (e.g. --set download_enabled=true "
            "--set comments_enabled=false). VALUE is JSON-decoded when possible."
        ),
    )


@command(
    "video",
    "settings",
    "Update settings on a Loom video such as download_enabled or comments_enabled.",
    configure=_settings_args,
    write=True,
)
async def video_settings(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    settings = parse_settings(ns.settings)
    if preview := dry(ns, "update_video_settings", video_id=vid, settings=settings):
        return preview
    return ok(await client.update_video_settings(vid, settings))


@command(
    "video",
    "delete",
    "Permanently delete a Loom video. This cannot be undone.\n\n"
    "To temporarily hide a video use 'loom video archive'; to bring back a\n"
    "recently deleted one use 'loom video recover'.",
    configure=A.video_id,
    write=True,
)
async def video_delete(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(ns, "delete_video", video_id=vid):
        return preview
    result = await client.delete_video(vid)
    return Result(data=result, text=f"Video deleted: {result}")


@command(
    "video",
    "archive",
    "Archive or unarchive Loom videos. Archived videos are hidden but not deleted.",
    configure=A.chain(
        A.video_ids,
        A.flag("archive", "archive", "Archive (default) or --no-archive to restore"),
    ),
    write=True,
)
async def video_archive(client: LoomClient, ns) -> Result:
    vids = check_ids(ns.video_ids, "video ID")
    if preview := dry(ns, "archive_videos", video_ids=vids, archive=ns.archive):
        return preview
    return ok(await client.archive_videos(vids, ns.archive))


@command(
    "video",
    "recover",
    "Recover a deleted Loom video from the trash.",
    configure=A.video_id,
    write=True,
)
async def video_recover(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(ns, "recover_video", video_id=vid):
        return preview
    return ok(await client.recover_video(vid))


@command(
    "video",
    "duplicate",
    "Duplicate a Loom video. Creates a new copy each time.",
    configure=A.video_id,
    write=True,
)
async def video_duplicate(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(ns, "duplicate_video", video_id=vid):
        return preview
    return ok(await client.duplicate_video(vid))


@command(
    "video",
    "pin",
    "Pin or unpin a Loom video in your library.",
    configure=A.chain(
        A.video_id, A.flag("pin", "pinned", "Pin (default) or --no-pin to unpin")
    ),
    write=True,
)
async def video_pin(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(ns, "update_video_pin_status", video_id=vid, pinned=ns.pinned):
        return preview
    await client.update_video_pin_status(vid, ns.pinned)
    action = "Pinned" if ns.pinned else "Unpinned"
    return Result(
        data={"video_id": vid, "pinned": ns.pinned}, text=f"{action} video {vid}"
    )


@command(
    "video",
    "follow",
    "Follow or unfollow a Loom video to get notifications.",
    configure=A.chain(
        A.video_id,
        A.flag("follow", "follow", "Follow (default) or --no-follow to unfollow"),
    ),
    write=True,
)
async def video_follow(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(ns, "toggle_following", video_id=vid, follow=ns.follow):
        return preview
    return ok(await client.toggle_following(vid, ns.follow))


def _move_videos_args(p):
    A.video_ids(p)
    p.add_argument(
        "--to",
        dest="folder_id",
        required=True,
        metavar="FOLDER_ID",
        help="The destination folder ID",
    )


@command(
    "video",
    "move",
    "Move one or more Loom videos into a different folder.",
    configure=_move_videos_args,
    write=True,
)
async def video_move(client: LoomClient, ns) -> Result:
    vids = check_ids(ns.video_ids, "video ID")
    folder = check_id(ns.folder_id, "folder ID")
    if preview := dry(ns, "bulk_move_videos", video_ids=vids, folder_id=folder):
        return preview
    return ok(await client.bulk_move_videos(vids, folder))


def _share_args(p):
    A.video_ids(p)
    p.add_argument(
        "--space",
        dest="space_ids",
        action="append",
        required=True,
        metavar="SPACE_ID",
        help="Destination space ID, repeatable (at least one required)",
    )


@command(
    "video",
    "share",
    "Share one or more Loom videos to one or more spaces.",
    configure=_share_args,
    write=True,
)
async def video_share(client: LoomClient, ns) -> Result:
    vids = check_ids(ns.video_ids, "video ID")
    spaces = check_ids(ns.space_ids, "space ID")
    if preview := dry(
        ns, "batch_share_videos_to_spaces", video_ids=vids, space_ids=spaces
    ):
        return preview
    return ok(await client.batch_share_videos_to_spaces(vids, spaces))


@command(
    "video",
    "regenerate-mp4",
    "Trigger MP4 regeneration for a Loom video.\n\n"
    "Use when 'loom video download-url' reports that no URL is available.\n"
    "Regeneration is asynchronous — wait ~30 seconds, then retry download-url.",
    configure=A.video_id,
    write=True,
)
async def video_regenerate_mp4(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(ns, "regenerate_mp4", video_id=vid):
        return preview
    result = await client.regenerate_mp4(vid)
    if result.get("message"):
        raise LoomCLIError(f"Failed to regenerate MP4: {result['message']}", kind="api")
    return ok(result)
