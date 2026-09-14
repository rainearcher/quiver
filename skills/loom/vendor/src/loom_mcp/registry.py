"""The command registry: a Command record plus the decorator that registers it."""

import argparse
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

Configure = Callable[[argparse.ArgumentParser], None]
Handler = Callable[[Any, argparse.Namespace], Awaitable[Any]]

#: Noun groups in the order they appear in ``loom --help``.
GROUPS: dict[str, str] = {
    "video": "Videos: list, search, read, and manage Loom recordings",
    "comment": "Comments on videos, plus comment reactions",
    "task": "Action items (tasks) extracted from videos",
    "reaction": "Emoji reactions on videos",
    "folder": "Folders in your Loom library",
    "space": "Spaces (workspaces) you belong to",
    "watch-later": "Your Watch Later list",
    "tag": "Workspace tags",
    "user": "Loom user profiles",
}

#: Fully-qualified ``"<group> <name>"`` -> Command.
COMMANDS: dict[str, "Command"] = {}


@dataclass(frozen=True)
class Command:
    group: str
    name: str
    help: str
    run: Handler
    configure: Configure | None = None
    write: bool = False

    @property
    def key(self) -> str:
        return f"{self.group} {self.name}"

    @property
    def summary(self) -> str:
        """First line of the help text, used in the subcommand listing."""
        return self.help.strip().splitlines()[0]


def command(
    group: str,
    name: str,
    help: str,  # noqa: A002 - mirrors argparse's own keyword
    configure: Configure | None = None,
    write: bool = False,
) -> Callable[[Handler], Handler]:
    """Register a handler as ``loom <group> <name>``."""

    def decorate(fn: Handler) -> Handler:
        if group not in GROUPS:
            raise KeyError(f"Unknown command group: {group!r}")
        cmd = Command(
            group=group,
            name=name,
            help=help.strip(),
            run=fn,
            configure=configure,
            write=write,
        )
        if cmd.key in COMMANDS:
            raise KeyError(f"Duplicate command: {cmd.key}")
        COMMANDS[cmd.key] = cmd
        return fn

    return decorate
