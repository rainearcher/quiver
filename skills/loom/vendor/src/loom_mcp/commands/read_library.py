"""Read commands for comments, reactions, folders, spaces, tags and users (11)."""

from loom_mcp import render
from loom_mcp.client import LoomClient
from loom_mcp.commands import args as A
from loom_mcp.commands.support import paged
from loom_mcp.errors import LoomCLIError, check_id
from loom_mcp.output import Result
from loom_mcp.registry import command


# --- comments --------------------------------------------------------------


@command(
    "comment",
    "reactions",
    "Get emoji reactions on a specific comment.",
    configure=A.chain(A.comment_id, A.comment_type),
)
async def comment_reactions(client: LoomClient, ns) -> Result:
    reactions = await client.get_comment_reactions(
        check_id(ns.comment_id, "comment ID"), ns.comment_type
    )
    if not reactions:
        return Result(data=[], note="No reactions on this comment.")
    return Result(data=reactions, text=render.comment_reactions_text(reactions))


# --- reactions -------------------------------------------------------------


@command(
    "reaction",
    "frequent",
    "Get your most frequently used emoji reaction types.\n\n"
    "Also useful to discover valid values for 'loom reaction add --type'.",
)
async def reaction_frequent(client: LoomClient, ns) -> Result:
    reactions = await client.get_frequent_reactions()
    if not reactions:
        return Result(data=[], note="No recent reactions.")
    return Result(data=reactions, text=render.frequent_reactions_text(reactions))


# --- folders ---------------------------------------------------------------


@command(
    "folder",
    "list",
    "List your Loom folders, sorted by most recent.",
    configure=A.paging(noun="folders"),
)
async def folder_list(client: LoomClient, ns) -> Result:
    folders = await paged(client.list_folders, "folders", ns.limit, ns.all)
    if not folders:
        return Result(data=[], note="No folders found.")
    return Result(data=folders, text=render.folders_table(folders))


@command(
    "folder",
    "search",
    "Search your Loom folders by name.",
    configure=A.query,
)
async def folder_search(client: LoomClient, ns) -> Result:
    folders = await client.search_folders(ns.query)
    if not folders:
        return Result(data=[], note=f"No folders matching '{ns.query}'")
    return Result(data=folders, text=render.folders_table(folders, visibility=False))


@command(
    "folder",
    "get",
    "Get details of a Loom folder including name, visibility and creator.",
    configure=A.folder_id,
)
async def folder_get(client: LoomClient, ns) -> Result:
    folder = await client.get_folder(check_id(ns.folder_id, "folder ID"))
    if not folder:
        raise LoomCLIError(f"Folder not found: {ns.folder_id}", kind="notfound")
    return Result(data=folder, text=render.pretty_json(folder))


# --- spaces ----------------------------------------------------------------


@command(
    "space",
    "list",
    "List your Loom spaces (workspaces).",
    configure=A.paging(default_all=True, noun="spaces"),
)
async def space_list(client: LoomClient, ns) -> Result:
    spaces = await paged(client.list_spaces, "spaces", ns.limit, ns.all)
    if not spaces:
        return Result(data=[], note="No spaces found.")
    return Result(data=spaces, text=render.spaces_table(spaces))


@command(
    "space",
    "get",
    "Get details of a Loom space: name, privacy level, and whether it is primary.",
    configure=A.space_id,
)
async def space_get(client: LoomClient, ns) -> Result:
    space = await client.get_space(check_id(ns.space_id, "space ID"))
    if not space:
        raise LoomCLIError(f"Space not found: {ns.space_id}", kind="notfound")
    return Result(data=space, text=render.pretty_json(space))


# --- watch later -----------------------------------------------------------


@command(
    "watch-later",
    "count",
    "Get the number of videos in your Watch Later list.",
)
async def watch_later_count(client: LoomClient, ns) -> Result:
    count = await client.get_watch_later_count()
    return Result(data=count, text=f"Watch Later list has {count} videos")


# --- tags ------------------------------------------------------------------


@command(
    "tag",
    "search",
    "Search for tags in your Loom workspace.\n\n"
    "Known limitation: Loom's tag search selection set returns only __typename,\n"
    "so rows carry no tag names yet.",
    configure=A.query,
)
async def tag_search(client: LoomClient, ns) -> Result:
    tags = await client.search_workspace_tags(ns.query)
    if not tags:
        return Result(data=[], note=f"No tags matching '{ns.query}'")
    return Result(data=tags, text=render.pretty_json(tags))


# --- users -----------------------------------------------------------------


@command(
    "user",
    "get",
    "Get a Loom user's profile by ID — name, email, company and avatar.",
    configure=A.user_id,
)
async def user_get(client: LoomClient, ns) -> Result:
    user = await client.get_user_by_id(check_id(ns.user_id, "user ID"))
    if not user:
        raise LoomCLIError(f"User not found: {ns.user_id}", kind="notfound")
    return Result(data=user, text=render.pretty_json(user))


@command(
    "user",
    "video-count",
    "Get the total number of videos created by a user.",
    configure=A.user_id,
)
async def user_video_count(client: LoomClient, ns) -> Result:
    count = await client.get_total_videos_count(check_id(ns.user_id, "user ID"))
    return Result(data=count, text=f"User has {count} videos")
