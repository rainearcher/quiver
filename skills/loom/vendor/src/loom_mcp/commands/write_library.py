"""Write commands for folders, Watch Later and tags (7 commands)."""

from loom_mcp.client import LoomClient
from loom_mcp.commands import args as A
from loom_mcp.commands.support import dry, ok
from loom_mcp.errors import check_id, check_ids
from loom_mcp.output import Result
from loom_mcp.registry import command


# --- folders ---------------------------------------------------------------


def _folder_create_args(p):
    p.add_argument("--name", required=True, metavar="TEXT", help="The folder name")


@command(
    "folder",
    "create",
    "Create a new Loom folder. Each call creates a new folder.",
    configure=_folder_create_args,
    write=True,
)
async def folder_create(client: LoomClient, ns) -> Result:
    if preview := dry(ns, "create_folder", name=ns.name):
        return preview
    return ok(await client.create_folder(ns.name))


def _folder_rename_args(p):
    A.folder_id(p)
    p.add_argument("--name", required=True, metavar="TEXT", help="The new folder name")


@command(
    "folder",
    "rename",
    "Rename a Loom folder.",
    configure=_folder_rename_args,
    write=True,
)
async def folder_rename(client: LoomClient, ns) -> Result:
    fid = check_id(ns.folder_id, "folder ID")
    if preview := dry(ns, "rename_folder", folder_id=fid, name=ns.name):
        return preview
    return ok(await client.rename_folder(fid, ns.name))


@command(
    "folder",
    "delete",
    "Delete one or more Loom folders. This cannot be undone.",
    configure=A.folder_ids,
    write=True,
)
async def folder_delete(client: LoomClient, ns) -> Result:
    fids = check_ids(ns.folder_ids, "folder ID")
    if preview := dry(ns, "delete_folders", folder_ids=fids):
        return preview
    return ok(await client.delete_folders(fids))


def _folder_move_args(p):
    A.folder_ids(p)
    p.add_argument(
        "--to",
        dest="destination_folder_id",
        required=True,
        metavar="FOLDER_ID",
        help="The destination parent folder ID",
    )


@command(
    "folder",
    "move",
    "Move one or more Loom folders into a different parent folder.",
    configure=_folder_move_args,
    write=True,
)
async def folder_move(client: LoomClient, ns) -> Result:
    fids = check_ids(ns.folder_ids, "folder ID")
    destination = check_id(ns.destination_folder_id, "folder ID")
    if preview := dry(
        ns, "bulk_move_folders", folder_ids=fids, destination_folder_id=destination
    ):
        return preview
    return ok(await client.bulk_move_folders(fids, destination))


# --- watch later -----------------------------------------------------------


def _watch_later_add_args(p):
    A.video_id(p)
    p.add_argument(
        "--minutes-from-utc",
        type=int,
        default=0,
        metavar="N",
        help="Timezone offset in minutes from UTC (default 0)",
    )


@command(
    "watch-later",
    "add",
    "Add a Loom video to your Watch Later list.",
    configure=_watch_later_add_args,
    write=True,
)
async def watch_later_add(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(
        ns,
        "add_to_watch_later",
        video_id=vid,
        minutes_from_utc=ns.minutes_from_utc,
    ):
        return preview
    return ok(await client.add_to_watch_later(vid, ns.minutes_from_utc))


@command(
    "watch-later",
    "remove",
    "Remove a Loom video from your Watch Later list.",
    configure=A.video_id,
    write=True,
)
async def watch_later_remove(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(ns, "remove_from_watch_later", video_id=vid):
        return preview
    return ok(await client.remove_from_watch_later(vid))


# --- tags ------------------------------------------------------------------


def _tag_follow_args(p):
    p.add_argument("tag", metavar="TAG", help="The tag name to follow or unfollow")
    A.flag("follow", "follow", "Follow (default) or --no-follow to unfollow")(p)


@command(
    "tag",
    "follow",
    "Follow or unfollow a tag in your Loom workspace to get notifications.",
    configure=_tag_follow_args,
    write=True,
)
async def tag_follow(client: LoomClient, ns) -> Result:
    if preview := dry(ns, "toggle_following_tag", tag=ns.tag, follow=ns.follow):
        return preview
    await client.toggle_following_tag(ns.tag, ns.follow)
    action = "Following" if ns.follow else "Unfollowed"
    return Result(
        data={"tag": ns.tag, "follow": ns.follow}, text=f"{action} tag '{ns.tag}'"
    )
