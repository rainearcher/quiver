"""Argument parsing and the process entrypoint for the ``loom`` CLI."""

import argparse
import asyncio
import os
import sys

import httpx

from loom_mcp import __version__, config, output
from loom_mcp.client import LoomAPIError
from loom_mcp.commands import COMMANDS, GROUPS
from loom_mcp.errors import ExitCode, LoomCLIError, exit_code_for, message_for

PROG = "loom"

DESCRIPTION = """\
Command-line client for Loom's internal GraphQL API.

Read videos, transcripts, summaries, chapters, comments and tasks, and manage
your library from the shell. Human-readable text by default; --json for the raw
payload.
"""

EPILOG = """\
authentication:
  Set LOOM_COOKIE to your browser's connect.sid value (the 'connect.sid=' prefix
  is added for you), or LOOM_AUTH_FILE to a Playwright storage-state JSON file.
  --cookie / --auth-file override both.

exit codes:
  0 success (including empty results)   3 auth / expired session
  1 Loom API or unexpected error        4 not found
  2 usage or invalid ID                 5 network, timeout or rate limit
"""

#: Defaults for the global flags. The flags themselves parse with SUPPRESS so a
#: value given before the subcommand is not clobbered by the leaf parser.
GLOBAL_DEFAULTS = {
    "json": False,
    "output": None,
    "save_dir": None,
    "quiet": False,
    "cookie": None,
    "auth_file": None,
    "timeout": 30.0,
    "dry_run": False,
}


def _global_options() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    g = p.add_argument_group("global options")
    g.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Print the raw payload as JSON instead of the human rendering",
    )
    g.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        default=argparse.SUPPRESS,
        help="Write the payload to PATH ('-' means stdout)",
    )
    g.add_argument(
        "--save-dir",
        metavar="DIR",
        default=argparse.SUPPRESS,
        help="Save video assets under DIR/<video_id>/ (video commands only)",
    )
    g.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Suppress notes and [Saved to ...] lines on stderr",
    )
    g.add_argument(
        "--cookie",
        metavar="VALUE",
        default=argparse.SUPPRESS,
        help="Loom session cookie, overriding $LOOM_COOKIE",
    )
    g.add_argument(
        "--auth-file",
        metavar="PATH",
        default=argparse.SUPPRESS,
        help="Playwright storage-state file, overriding $LOOM_AUTH_FILE",
    )
    g.add_argument(
        "--timeout",
        type=float,
        metavar="SECONDS",
        default=argparse.SUPPRESS,
        help="HTTP timeout in seconds (default 30)",
    )
    g.add_argument(
        "--dry-run",
        action="store_true",
        default=argparse.SUPPRESS,
        help="For write commands: print the resolved operation and exit without calling Loom",
    )
    return p


def build_parser() -> argparse.ArgumentParser:
    """Build the two-level ``loom <group> <command>`` parser tree."""
    globals_parser = _global_options()
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=DESCRIPTION,
        epilog=EPILOG,
        parents=[globals_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"{PROG} {__version__}")

    groups = parser.add_subparsers(dest="_group", metavar="GROUP", required=True)
    for group, description in GROUPS.items():
        group_parser = groups.add_parser(
            group,
            help=description,
            description=description,
            parents=[globals_parser],
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        leaves = group_parser.add_subparsers(
            dest="_name", metavar="COMMAND", required=True
        )
        for cmd in _group_commands(group):
            leaf = leaves.add_parser(
                cmd.name,
                help=cmd.summary,
                description=cmd.help,
                parents=[globals_parser],
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )
            if cmd.configure is not None:
                cmd.configure(leaf)
            leaf.set_defaults(_cmd=cmd.key)
    return parser


def _group_commands(group: str):
    return [c for c in COMMANDS.values() if c.group == group]


def _apply_global_defaults(ns: argparse.Namespace) -> argparse.Namespace:
    for key, value in GLOBAL_DEFAULTS.items():
        if not hasattr(ns, key):
            setattr(ns, key, value)
    return ns


async def _run(ns: argparse.Namespace) -> int:
    client = config.resolve_auth(ns.cookie, ns.auth_file, timeout=ns.timeout)
    try:
        result = await COMMANDS[ns._cmd].run(client, ns)
        output.emit(result, ns)
        return int(ExitCode.OK)
    finally:
        await client.aclose()


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv``, run one command, and return the process exit code."""
    ns = _apply_global_defaults(build_parser().parse_args(argv))
    try:
        return asyncio.run(_run(ns))
    except KeyboardInterrupt:
        return int(ExitCode.INTERRUPT)
    except (
        LoomCLIError,
        LoomAPIError,
        httpx.HTTPError,
        ValueError,
        OSError,
    ) as exc:
        if os.environ.get("LOOM_DEBUG"):
            raise
        output.error(message_for(exc))
        return exit_code_for(exc)


if __name__ == "__main__":
    sys.exit(main())
