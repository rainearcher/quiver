"""Reusable argparse types and argument configurators shared by the handlers."""

import argparse
import sys


def bounded_int(low: int, high: int | None = None):
    """argparse type enforcing the ge/le bounds pydantic used to enforce."""

    def parse(raw: str) -> int:
        try:
            value = int(raw)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{raw!r} is not an integer") from None
        if value < low or (high is not None and value > high):
            bounds = f"{low}..{high}" if high is not None else f">= {low}"
            raise argparse.ArgumentTypeError(f"must be {bounds}, got {value}")
        return value

    return parse


limit_type = bounded_int(1, 200)
nonneg_int = bounded_int(0)

COMMENT_TYPES = ("COMMENT", "REPLY")


def read_text(value: str) -> str:
    """Return ``value``, or the whole of stdin when it is exactly ``-``."""
    if value == "-":
        return sys.stdin.read()
    return value


# --- positional IDs --------------------------------------------------------


def video_id(p: argparse.ArgumentParser) -> None:
    p.add_argument("video_id", metavar="VIDEO_ID", help="The Loom video ID")


def video_ids(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "video_ids", metavar="VIDEO_ID", nargs="+", help="One or more Loom video IDs"
    )


def folder_id(p: argparse.ArgumentParser) -> None:
    p.add_argument("folder_id", metavar="FOLDER_ID", help="The Loom folder ID")


def folder_ids(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "folder_ids", metavar="FOLDER_ID", nargs="+", help="One or more Loom folder IDs"
    )


def space_id(p: argparse.ArgumentParser) -> None:
    p.add_argument("space_id", metavar="SPACE_ID", help="The Loom space ID")


def comment_id(p: argparse.ArgumentParser) -> None:
    p.add_argument("comment_id", metavar="COMMENT_ID", help="The comment GUID")


def task_id(p: argparse.ArgumentParser) -> None:
    p.add_argument("task_id", metavar="TASK_ID", help="The task ID")


def user_id(p: argparse.ArgumentParser) -> None:
    p.add_argument("user_id", metavar="USER_ID", help="The Loom user ID")


def query(p: argparse.ArgumentParser) -> None:
    p.add_argument("query", metavar="QUERY", help="Search query")


# --- shared option groups --------------------------------------------------


def paging(default_all: bool = False, noun: str = "items"):
    """``--limit`` plus ``--all/--no-all`` for the four paginated commands."""

    def configure(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--limit",
            type=limit_type,
            default=50,
            metavar="N",
            help=f"Max {noun} to return, 1-200 (default 50)",
        )
        p.add_argument(
            "--all",
            action=argparse.BooleanOptionalAction,
            default=default_all,
            help=f"Drain every page instead of stopping at --limit (default: {default_all})",
        )

    return configure


def comment_type(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--type",
        dest="comment_type",
        choices=COMMENT_TYPES,
        default="COMMENT",
        help="Comment type (default COMMENT)",
    )


def content(p: argparse.ArgumentParser, help_text: str) -> None:
    p.add_argument(
        "--content",
        required=True,
        metavar="TEXT",
        help=f"{help_text} ('-' reads stdin)",
    )


def timestamp(p: argparse.ArgumentParser, help_text: str) -> None:
    p.add_argument(
        "--timestamp",
        type=nonneg_int,
        default=0,
        metavar="N",
        help=f"{help_text} (default 0)",
    )


def flag(name: str, dest: str, help_text: str, default: bool = True):
    """A ``--x/--no-x`` pair backed by BooleanOptionalAction."""

    def configure(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            f"--{name}",
            dest=dest,
            action=argparse.BooleanOptionalAction,
            default=default,
            help=help_text,
        )

    return configure


def chain(*configurators):
    """Compose several configurators into one."""

    def configure(p: argparse.ArgumentParser) -> None:
        for c in configurators:
            c(p)

    return configure
