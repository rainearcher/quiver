# loom

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Command-line client for Loom's internal GraphQL API. Read videos, transcripts, captions, AI summaries, chapters, comments and tasks — and manage your library — straight from the shell. Human-readable text by default, `--json` for the raw payload, so it composes with `jq`, pipes, and scripts.

## Features

- List, search, and read Loom videos, including a one-shot `video details` that fetches metadata, transcript, chapters, summary, tasks and comments concurrently
- Read transcripts, WebVTT captions, AI summaries, chapters, key takeaways and descriptions
- Save any fetched content to disk with `--save-dir`
- Manage comments, tasks, reactions and tags
- Organize with folders, spaces and your Watch Later list
- Rename videos, update settings and descriptions, move, share, archive, pin and follow
- `--json` on every command, meaningful exit codes, and `--dry-run` on every write

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (or any tool that can install a Python package)

## Install

> **PyPI is not up to date.** The published `mcp-loom` release is **1.2.0**, which ships the old MCP server (`loom-mcp`), not this CLI. `uv tool install mcp-loom` will *not* give you `loom` until 2.0.0 is tagged and published. Install from git until then.

Install it once as a tool, so `loom` is on your `PATH`:

```sh
uv tool install git+https://github.com/rainearcher/mcp-loom.git
loom --help
```

Or run it without installing anything permanently:

```sh
uvx --from git+https://github.com/rainearcher/mcp-loom.git loom video list
```

The distribution is named `mcp-loom`; the command it provides is `loom`.

You can also get the CLI without touching this repo at all: the [`loom` skill in quiver](https://github.com/rainearcher/quiver/tree/main/skills/loom) vendors a copy, so installing that skill installs the tool.

To work from a clone:

```sh
git clone https://github.com/karbassi/loom-mcp.git
cd loom-mcp
uv sync
uv run loom --help
```

## Authentication

> [!IMPORTANT]
> Loom has no official API key. This tool talks to Loom's internal GraphQL API using your browser session cookie, which you have to copy out of your browser yourself.

1. Open [loom.com](https://www.loom.com) in your browser and sign in
2. Open DevTools (F12) → Application → Cookies → `https://www.loom.com`
3. Copy the **value** of the `connect.sid` cookie (it starts with `s%3A...`)
4. Export it as `LOOM_COOKIE`:

```sh
export LOOM_COOKIE='s%3A...'
```

The `connect.sid=` prefix is added for you, so either `s%3A...` or `connect.sid=s%3A...` works. Put the export in your shell profile (or a `.env` file next to the project root) to make it stick. The cookie lasts about 30 days; when it expires, commands exit `3` and tell you to grab a fresh one.

Alternatives to the env var:

- `--cookie VALUE` — pass the cookie inline, overriding `$LOOM_COOKIE`
- `LOOM_AUTH_FILE=/path/to/auth.json` or `--auth-file PATH` — a [Playwright storage-state](https://playwright.dev/docs/auth) JSON file

## Usage

Commands are `loom <group> <command>`, where the group is the noun you are acting on:

```
loom video          Videos: list, search, read, and manage Loom recordings
loom comment        Comments on videos, plus comment reactions
loom task           Action items (tasks) extracted from videos
loom reaction       Emoji reactions on videos
loom folder         Folders in your Loom library
loom space          Spaces (workspaces) you belong to
loom watch-later    Your Watch Later list
loom tag            Workspace tags
loom user           Loom user profiles
```

Every level has help: `loom --help`, `loom video --help`, `loom video transcript --help`.

```sh
# What did I record recently?
loom video list --limit 10

# Find it, then read it
loom video search "quarterly review"
loom video transcript 1a2b3c4d5e6f7890abcdef1234567890

# Everything about one video in a single call, saved to disk
loom video details 1a2b3c4d5e6f7890abcdef1234567890 --save-dir ./notes
```

### Global options

These work on every command, and may be given before or after the subcommand (`loom --json video list` and `loom video list --json` are the same).

| Flag | Effect |
|---|---|
| `--json` | Print the raw payload as JSON instead of the human rendering |
| `-o PATH`, `--output PATH` | Write the payload to `PATH` (`-` means stdout) |
| `--save-dir DIR` | Save video assets under `DIR/<video_id>/` (video commands only) |
| `-q`, `--quiet` | Suppress notes and `[Saved to ...]` lines on stderr |
| `--cookie VALUE` | Loom session cookie, overriding `$LOOM_COOKIE` |
| `--auth-file PATH` | Playwright storage-state file, overriding `$LOOM_AUTH_FILE` |
| `--timeout SECONDS` | HTTP timeout in seconds (default 30) |
| `--dry-run` | On write commands: print the resolved operation and exit without calling Loom |
| `--version` | Print the version |

Text output goes to stdout; notes, `[Saved to ...]` lines and errors go to stderr, so piping stdout stays clean.

### JSON output

`--json` prints the payload as JSON, ready for `jq`:

```sh
loom video list --limit 50 --json | jq -r '.[] | "\(.id)\t\(.name)"'
loom video comments 1a2b3c4d5e6f7890abcdef1234567890 --json | jq length
```

List-shaped reads (comments, tasks, reactions, tags, search results, folder and space listings) print `[]` when empty, so `jq length` and `for` loops always work. Scalar reads that have no value (a video with no transcript, no summary, no download URL) print `null` and write an explanatory note to stderr. Neither case is an error — both exit `0`.

### Dry runs

Every write command accepts `--dry-run`, which validates the arguments and prints the operation it *would* send, without touching your Loom data:

```sh
loom video delete 1a2b3c4d5e6f7890abcdef1234567890 --dry-run
```

### Reading text from stdin

Flags that take free text (`--content`, `--description`) accept `-` to read the whole of stdin:

```sh
loom comment add 1a2b3c4d5e6f7890abcdef1234567890 --content - < review.md
pbpaste | loom video set-description 1a2b3c4d5e6f7890abcdef1234567890 --description -
```

## Commands

`VIDEO_ID` below is the hex ID from a Loom URL: `https://www.loom.com/share/<VIDEO_ID>`.

### `loom video` — read

| Command | Description | `--save-dir` file |
|---|---|---|
| `loom video list [--limit N] [--all]` | List your videos, most recent first | |
| `loom video search QUERY [--limit N] [--all]` | Search videos by keyword | |
| `loom video get VIDEO_ID` | Metadata: name, duration, owner, views, created date | `metadata.json` |
| `loom video details VIDEO_ID` | Metadata, transcript, chapters, summary, tasks and comments in one call, rendered as markdown | `details.md` + `metadata.json`, `transcript.txt`, `chapters.txt`, `summary.txt`, `tasks.txt`, `comments.txt` |
| `loom video transcript VIDEO_ID` | Full transcript with timestamps and speakers | `transcript.txt` |
| `loom video captions VIDEO_ID` | WebVTT captions with start+end times per cue | `captions.vtt` |
| `loom video summary VIDEO_ID` | AI-generated summary | `summary.txt` |
| `loom video chapters VIDEO_ID` | AI-generated chapter markers | `chapters.txt` |
| `loom video takeaways VIDEO_ID` | AI-generated key takeaways | `takeaways.txt` |
| `loom video description VIDEO_ID` | AI-generated description with timestamped sections | `description.txt` |
| `loom video tags VIDEO_ID` | Tags on the video | `tags.txt` |
| `loom video comments VIDEO_ID` | Comments and threaded replies | `comments.txt` |
| `loom video tasks VIDEO_ID` | AI-generated action items | `tasks.txt` |
| `loom video reactions VIDEO_ID` | Emoji reactions, with who and when | `reactions.txt` |
| `loom video backlinks VIDEO_ID` | Where the video is shared or embedded | `backlinks.txt` |
| `loom video confluence VIDEO_ID` | Linked Confluence pages | |
| `loom video meeting-notes VIDEO_ID` | Confluence meeting notes URL | |
| `loom video download-url VIDEO_ID` | Signed MP4 download URL | |
| `loom video watch-time VIDEO_ID` | Last timestamp where you stopped watching | |

```sh
loom video list --all --json > all-videos.json
loom video captions 1a2b3c4d5e6f7890abcdef1234567890 -o captions.vtt
loom video summary 1a2b3c4d5e6f7890abcdef1234567890
```

`--limit N` takes 1–200 and defaults to 50. `--all` drains every page instead, ignoring `--limit`.

### `loom video` — write

| Command | Description |
|---|---|
| `loom video rename VIDEO_ID --name TEXT` | Rename a video |
| `loom video set-description VIDEO_ID --description TEXT\|-` | Overwrite the description |
| `loom video settings VIDEO_ID --set KEY=VALUE` | Update settings; repeatable, `VALUE` is JSON-decoded when possible |
| `loom video delete VIDEO_ID` | Permanently delete a video — cannot be undone |
| `loom video archive VIDEO_ID... [--no-archive]` | Archive (default) or unarchive videos |
| `loom video recover VIDEO_ID` | Recover a deleted video from the trash |
| `loom video duplicate VIDEO_ID` | Duplicate a video |
| `loom video pin VIDEO_ID [--no-pin]` | Pin or unpin a video in your library |
| `loom video follow VIDEO_ID [--no-follow]` | Follow or unfollow a video |
| `loom video move VIDEO_ID... --to FOLDER_ID` | Move videos into a folder |
| `loom video share VIDEO_ID... --space SPACE_ID` | Share videos to one or more spaces (repeat `--space`) |
| `loom video regenerate-mp4 VIDEO_ID` | Trigger MP4 regeneration |

```sh
loom video rename 1a2b3c4d5e6f7890abcdef1234567890 --name "Q3 retro"
loom video settings 1a2b3c4d5e6f7890abcdef1234567890 --set download_enabled=true --set comments_enabled=false
loom video move 1a2b... 9f8e... --to my_folder.v2
loom video share 1a2b... --space sp_123 --space sp_456
```

If `loom video download-url` returns nothing, the MP4 has not been rendered yet — run `loom video regenerate-mp4 VIDEO_ID`, wait ~30 seconds, and ask again.

### `loom comment`

| Command | Description |
|---|---|
| `loom comment reactions COMMENT_ID [--type COMMENT\|REPLY]` | Emoji reactions on a comment |
| `loom comment add VIDEO_ID --content TEXT\|- [--timestamp N]` | Post a comment, optionally at a timestamp |
| `loom comment edit COMMENT_ID --video VIDEO_ID --content TEXT\|-` | Overwrite a comment's text |
| `loom comment delete COMMENT_ID [--type COMMENT\|REPLY]` | Delete a comment — cannot be undone |
| `loom comment react COMMENT_ID --reaction EMOJI [--type COMMENT\|REPLY]` | React to a comment |

```sh
loom comment add 1a2b3c4d5e6f7890abcdef1234567890 --content "Nice walkthrough" --timestamp 42
loom comment react 0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0 --reaction "🎉"
```

### `loom task`

| Command | Description |
|---|---|
| `loom task add VIDEO_ID --content TEXT\|- [--timestamp N]` | Create an action item |
| `loom task update TASK_ID --content TEXT\|-` | Update an action item's text |
| `loom task delete TASK_ID` | Delete an action item — cannot be undone |
| `loom task approve TASK_ID` | Mark an action item approved |
| `loom task respond TASK_ID [--no-responded]` | Mark an action item responded (or not) |

```sh
loom task add 1a2b3c4d5e6f7890abcdef1234567890 --content "Send the deck to design" --timestamp 128
loom task approve 4815162342
```

### `loom reaction`

| Command | Description |
|---|---|
| `loom reaction frequent` | Your most-used emoji reaction types |
| `loom reaction add VIDEO_ID --time N --type TYPE` | React to a video at a timestamp |
| `loom reaction delete REACTION_ID` | Delete a reaction |

```sh
loom reaction add 1a2b3c4d5e6f7890abcdef1234567890 --time 90 --type LOVE
```

### `loom folder`

| Command | Description |
|---|---|
| `loom folder list [--limit N] [--all]` | List your folders, most recent first |
| `loom folder search QUERY` | Search folders by name |
| `loom folder get FOLDER_ID` | Folder details: name, visibility, creator |
| `loom folder create --name TEXT` | Create a folder |
| `loom folder rename FOLDER_ID --name TEXT` | Rename a folder |
| `loom folder delete FOLDER_ID...` | Delete folders — cannot be undone |
| `loom folder move FOLDER_ID... --to FOLDER_ID` | Move folders into a parent folder |

```sh
loom folder create --name "Customer calls"
loom folder search customer --json | jq -r '.[].id'
```

### `loom space`

| Command | Description |
|---|---|
| `loom space list [--limit N] [--no-all]` | List your spaces (drains every page by default) |
| `loom space get SPACE_ID` | Space details: name, privacy, whether it is primary |

### `loom watch-later`

| Command | Description |
|---|---|
| `loom watch-later count` | Number of videos in your Watch Later list |
| `loom watch-later add VIDEO_ID [--minutes-from-utc N]` | Add a video |
| `loom watch-later remove VIDEO_ID` | Remove a video |

### `loom tag`

| Command | Description |
|---|---|
| `loom tag search QUERY` | Search workspace tags |
| `loom tag follow TAG [--no-follow]` | Follow or unfollow a workspace tag |

> [!NOTE]
> `loom tag search` currently returns rows with no names — Loom's tag-search selection set only gives back `__typename`. The command is kept for parity; treat its output as a count, not a list.

### `loom user`

| Command | Description |
|---|---|
| `loom user get USER_ID` | Profile: name, email, company, avatar |
| `loom user video-count USER_ID` | Total videos created by a user |

## Saving to disk

`--save-dir DIR` writes a video command's output to `DIR/<video_id>/<canonical-name>` and prints `[Saved to ...]` on stderr. The filename is fixed per command (see the `--save-dir` column above), so repeated runs overwrite in place and a directory of videos ends up uniformly laid out.

```sh
loom video transcript 1a2b3c4d5e6f7890abcdef1234567890 --save-dir ./notes
# writes ./notes/1a2b3c4d5e6f7890abcdef1234567890/transcript.txt
```

`loom video details` saves each piece individually (`metadata.json`, `transcript.txt`, `summary.txt`, `chapters.txt`, `tasks.txt`, `comments.txt`) plus a combined `details.md`.

Use `-o PATH` instead when you want one specific file at a path of your choosing; `-o` works on every command, `--save-dir` only on video commands.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success, including empty results |
| `1` | Loom API error, or an unexpected failure |
| `2` | Usage error or invalid ID |
| `3` | Auth failure — missing cookie, or an expired session |
| `4` | Not found |
| `5` | Network error, timeout, or rate limit |
| `130` | Interrupted (Ctrl-C) |

An empty read is a success, not an error, so scripts can tell "no comments" apart from "that video does not exist":

```sh
if ! loom video get "$id" >/dev/null; then
  case $? in
    3) echo "cookie expired" ;;
    4) echo "no such video" ;;
    *) echo "something else went wrong" ;;
  esac
fi
```

## Upgrading from 1.x

Version 1.x shipped an MCP server (`loom-mcp`) that exposed these same operations as tools. 2.0 replaces it with this CLI: there is no MCP transport, no `mcpServers` configuration, and no `fastmcp` dependency. Remove the `loom` entry from your MCP client config, uninstall the old console script, and install the CLI as above. Every former tool has a subcommand — `get_transcript` is `loom video transcript`, `search_videos` is `loom video search`, `update_video_name` is `loom video rename`, and so on; the tables above list all of them. The `save_dir` tool parameter is now the `--save-dir` flag, and it behaves identically.

## Troubleshooting

**Exit code 3 / "session has expired"** — your `connect.sid` cookie has aged out (~30 days). Grab a fresh one using the steps in [Authentication](#authentication).

**Exit code 5 / timeouts** — Loom's API is slow or rate-limiting. Raise the deadline with `--timeout 60`, or retry in a moment.

**`loom: command not found`** — `uv tool install` puts it in uv's tool bin directory; run `uv tool update-shell` (then restart your shell), or use `uvx --from git+https://github.com/rainearcher/mcp-loom.git loom ...` instead. If you installed from PyPI you got 1.2.0, which provides `loom-mcp` rather than `loom` — see [Install](#install).

**Tracebacks instead of a clean error line** — set `LOOM_DEBUG=1` to get the full traceback on purpose; unset it for the one-line form.

## Contributing

Issues and pull requests are welcome on [GitHub](https://github.com/karbassi/loom-mcp). See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
