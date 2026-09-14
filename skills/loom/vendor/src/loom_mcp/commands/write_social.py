"""Write commands for comments, tasks and reactions (11 commands)."""

from loom_mcp.client import LoomClient
from loom_mcp.commands import args as A
from loom_mcp.commands.support import dry, ok
from loom_mcp.errors import LoomCLIError, check_id
from loom_mcp.output import Result
from loom_mcp.registry import command


# --- comments --------------------------------------------------------------


def _comment_add_args(p):
    A.video_id(p)
    A.content(p, "The comment text")
    A.timestamp(p, "Timestamp in seconds to attach the comment to")


@command(
    "comment",
    "add",
    "Post a comment on a Loom video. Each call creates a new comment.",
    configure=_comment_add_args,
    write=True,
)
async def comment_add(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    content = A.read_text(ns.content)
    if preview := dry(
        ns,
        "create_comment",
        video_id=vid,
        content=content,
        timestamp=ns.timestamp,
    ):
        return preview
    return ok(await client.create_comment(vid, content, ns.timestamp))


def _comment_edit_args(p):
    A.comment_id(p)
    p.add_argument(
        "--video",
        dest="video_id",
        required=True,
        metavar="VIDEO_ID",
        help="The Loom video ID the comment belongs to",
    )
    A.content(p, "The new comment text")


@command(
    "comment",
    "edit",
    "Edit an existing comment on a Loom video. Overwrites the comment text.",
    configure=_comment_edit_args,
    write=True,
)
async def comment_edit(client: LoomClient, ns) -> Result:
    cid = check_id(ns.comment_id, "comment ID")
    vid = check_id(ns.video_id, "video ID")
    content = A.read_text(ns.content)
    if preview := dry(
        ns, "edit_comment", comment_id=cid, video_id=vid, content=content
    ):
        return preview
    return ok(await client.edit_comment(cid, vid, content))


@command(
    "comment",
    "delete",
    "Delete a comment from a Loom video. This cannot be undone.",
    configure=A.chain(A.comment_id, A.comment_type),
    write=True,
)
async def comment_delete(client: LoomClient, ns) -> Result:
    cid = check_id(ns.comment_id, "comment ID")
    if preview := dry(
        ns, "delete_comment", comment_id=cid, comment_type=ns.comment_type
    ):
        return preview
    result = await client.delete_comment(cid, ns.comment_type)
    return Result(data=result, text=f"Comment deleted: {result}")


def _comment_react_args(p):
    A.comment_id(p)
    p.add_argument(
        "--reaction",
        required=True,
        metavar="EMOJI",
        help="The reaction emoji string (e.g. 'heart', '+1', 'fire')",
    )
    A.comment_type(p)


@command(
    "comment",
    "react",
    "Add an emoji reaction to a comment on a Loom video.",
    configure=_comment_react_args,
    write=True,
)
async def comment_react(client: LoomClient, ns) -> Result:
    cid = check_id(ns.comment_id, "comment ID")
    if preview := dry(
        ns,
        "add_comment_reaction",
        comment_id=cid,
        reaction=ns.reaction,
        comment_type=ns.comment_type,
    ):
        return preview
    return ok(await client.add_comment_reaction(cid, ns.reaction, ns.comment_type))


# --- tasks -----------------------------------------------------------------


def _task_add_args(p):
    A.video_id(p)
    A.content(p, "The task/action item text")
    A.timestamp(p, "Timestamp in seconds to attach the task to")


@command(
    "task",
    "add",
    "Create an action item (task) on a Loom video. Each call creates a new task.",
    configure=_task_add_args,
    write=True,
)
async def task_add(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    content = A.read_text(ns.content)
    if preview := dry(
        ns, "create_task", video_id=vid, content=content, timestamp=ns.timestamp
    ):
        return preview
    return ok(await client.create_task(vid, content, ns.timestamp))


def _task_update_args(p):
    A.task_id(p)
    A.content(p, "The new task content")


@command(
    "task",
    "update",
    "Update the content of an action item (task) on a Loom video.",
    configure=_task_update_args,
    write=True,
)
async def task_update(client: LoomClient, ns) -> Result:
    tid = check_id(ns.task_id, "task ID")
    content = A.read_text(ns.content)
    if preview := dry(ns, "update_video_task", task_id=tid, content=content):
        return preview
    return ok(await client.update_video_task(tid, content))


@command(
    "task",
    "delete",
    "Delete an action item (task) from a Loom video. This cannot be undone.",
    configure=A.task_id,
    write=True,
)
async def task_delete(client: LoomClient, ns) -> Result:
    tid = check_id(ns.task_id, "task ID")
    if preview := dry(ns, "delete_task", task_id=tid):
        return preview
    return ok(await client.delete_task(tid))


@command(
    "task",
    "approve",
    "Mark an action item (task) as approved on a Loom video.",
    configure=A.task_id,
    write=True,
)
async def task_approve(client: LoomClient, ns) -> Result:
    tid = check_id(ns.task_id, "task ID")
    if preview := dry(ns, "approve_task", task_id=tid):
        return preview
    return ok(await client.approve_task(tid))


@command(
    "task",
    "respond",
    "Respond to an action item (task) on a Loom video.",
    configure=A.chain(
        A.task_id,
        A.flag(
            "responded",
            "responded",
            "Mark as responded (default) or --no-responded to unmark",
        ),
    ),
    write=True,
)
async def task_respond(client: LoomClient, ns) -> Result:
    tid = check_id(ns.task_id, "task ID")
    if preview := dry(ns, "respond_to_task", task_id=tid, responded=ns.responded):
        return preview
    return ok(await client.respond_to_task(tid, ns.responded))


# --- reactions -------------------------------------------------------------


def _reaction_add_args(p):
    A.video_id(p)
    p.add_argument(
        "--time",
        type=A.nonneg_int,
        required=True,
        metavar="N",
        help="Timestamp in seconds for the reaction",
    )
    p.add_argument(
        "--type",
        dest="reaction_type",
        required=True,
        metavar="TYPE",
        help="The reaction type — see 'loom reaction frequent' for valid values",
    )


@command(
    "reaction",
    "add",
    "Add an emoji reaction to a Loom video at a specific timestamp.\n\n"
    "Use 'loom reaction frequent' to discover valid reaction type values.",
    configure=_reaction_add_args,
    write=True,
)
async def reaction_add(client: LoomClient, ns) -> Result:
    vid = check_id(ns.video_id, "video ID")
    if preview := dry(
        ns,
        "add_reaction",
        video_id=vid,
        time=ns.time,
        reaction_type=ns.reaction_type,
    ):
        return preview
    result = await client.add_reaction(vid, ns.time, ns.reaction_type)
    if result.get("message"):
        raise LoomCLIError(f"Failed to add reaction: {result['message']}", kind="api")
    return ok(result)


def _reaction_delete_args(p):
    p.add_argument("reaction_id", metavar="REACTION_ID", help="The reaction ID")


@command(
    "reaction",
    "delete",
    "Delete an emoji reaction from a Loom video.",
    configure=_reaction_delete_args,
    write=True,
)
async def reaction_delete(client: LoomClient, ns) -> Result:
    rid = check_id(ns.reaction_id, "reaction ID")
    if preview := dry(ns, "delete_reaction", reaction_id=rid):
        return preview
    result = await client.delete_reaction(rid)
    return Result(data=result, text=f"Reaction deleted: {result}")
