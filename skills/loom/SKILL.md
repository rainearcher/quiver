---
name: loom
description: Read and manage Loom videos from the shell via the `loom` CLI, which ships inside this skill (nothing to install). Use whenever the user pastes a loom.com URL or mentions a Loom recording — "summarize this loom", "what did they say in this loom", "pull the transcript of this Loom video", "get the captions/chapters/key takeaways", "what are the action items from this recording", "extract to-dos from my last 10 looms", "list my Loom videos", "search my Looms for X", "who commented on this loom", "download this Loom video", "what's the download URL", "turn this Loom into meeting notes", "rename/archive/move/pin this video", "add a comment at 2:30". Handles transcripts, WebVTT captions, AI summaries, chapter markers, key takeaways, descriptions, comments and threaded replies, AI-extracted tasks, emoji reactions, backlinks, MP4 download URLs, plus library management across videos, folders, spaces, Watch Later and tags. Human-readable text by default, `--json` for parsing, `-o PATH` for long transcripts, `--dry-run` on every write. Requires LOOM_COOKIE (a browser `connect.sid` session cookie) — Loom has no official API key.
metadata:
  author: Raine Soriano (@rainearcher)
  version: "1.0.0"
---

# Loom CLI

`loom` is a command-line client for Loom's internal GraphQL API. It reads videos, transcripts, captions, AI summaries, chapters, key takeaways, comments and action items, and manages your library — all from the shell, with `--json` on every command so output composes with `jq`.

There is no MCP server and nothing to configure in `.mcp.json`. You call the CLI with `Bash`.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) on PATH (provides `uvx`), **or** `loom` already installed on PATH
- `LOOM_COOKIE` — your Loom browser session cookie

The CLI itself is **vendored into this skill** at `vendor/`, so there is nothing to install and nothing is fetched from PyPI. `uvx` builds that local copy the first time and caches it.

Loom has no official API key, so the tool talks to Loom as you, using your browser session cookie. Getting one:

1. Open [loom.com](https://www.loom.com) in a browser and sign in
2. DevTools (F12) → Application → Cookies → `https://www.loom.com`
3. Copy the **value** of the `connect.sid` cookie (it starts with `s%3A`)
4. `export LOOM_COOKIE='s%3A...'`

The `connect.sid=` prefix is added automatically, so either `s%3A...` or `connect.sid=s%3A...` works. Make it permanent by adding the `export` to `~/.zshrc` / `~/.bashrc` or `~/.claude/.env`, then restarting the CLI. The cookie lasts roughly 30 days; when it expires every command exits `3`.

Alternatives: `--cookie VALUE` passes a cookie inline, and `LOOM_AUTH_FILE` / `--auth-file PATH` accepts a [Playwright storage-state](https://playwright.dev/docs/auth) JSON file.

Verify everything once, on first use in a project:

```bash
bash ./scripts/check-setup.sh
```

It prints ✓/✗ per requirement, makes one live read-only call to prove the session works, and exits 0 when ready. If it fails, surface its output to the user and stop — do not start guessing at commands.

## Invocation contract

Always go through `scripts/loom.sh`, the wrapper that ships beside this file. It locates the vendored CLI relative to **its own** path, so it works from any working directory — do not try to `cd` anywhere first, and do not invoke `uvx` yourself.

This skill is installed to a different path depending on how it was obtained, and `CLAUDE_PLUGIN_ROOT` is not set for plain `Bash` calls. So resolve the wrapper once per session, then reuse `$LOOM` for every call:

```bash
# Plugin installs land in ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/;
# pick the highest version if several are present.
cached=$(ls -d ~/.claude/plugins/cache/*/loom/*/skills/loom 2>/dev/null | sort -V | tail -1)

for d in \
  "${CLAUDE_PLUGIN_ROOT:-/nonexistent}/skills/loom" \
  "$cached" \
  ~/.claude/skills/loom \
  .claude/skills/loom \
  ./skills/loom
do
  [ -n "$d" ] && [ -f "$d/scripts/loom.sh" ] && LOOM="bash $d/scripts/loom.sh" && break
done

if [ -z "${LOOM:-}" ]; then
  # Last resort: search the Claude config dir wherever the skill ended up.
  found=$(find ~/.claude -path '*/skills/loom/scripts/loom.sh' -print -quit 2>/dev/null)
  [ -n "$found" ] && LOOM="bash $found"
fi

[ -z "${LOOM:-}" ] && { echo "loom skill not found on disk" >&2; exit 1; }
$LOOM --version
```

The first call builds the vendored package (well under a second); every later call in the session is ~0.1s. If the user already has `loom` on PATH and prefers it, `LOOM_BIN=loom` makes the wrapper defer to it.

### Turning a pasted URL into a VIDEO_ID

Every command takes the bare hex ID, **not** a URL. Passing a URL fails with exit `2` (invalid ID), because IDs are restricted to `[A-Za-z0-9_.-]`. Strip it first:

```bash
loom_id() { printf '%s' "$1" | sed -E 's#.*loom\.com/(share|embed)/##; s#[?/#].*##'; }

VIDEO_ID=$(loom_id "https://www.loom.com/share/1a2b3c4d5e6f7890abcdef1234567890?sid=abc")
# -> 1a2b3c4d5e6f7890abcdef1234567890
```

This handles `/share/` and `/embed/` links and drops any `?sid=` tracking query.

## Global options

These work on every command and may be given **before or after** the subcommand — `loom --json video list` and `loom video list --json` are identical.

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

## Command reference

60 commands across 9 groups. `R` = read, `W` = write (honours `--dry-run`). Every level has help: `loom --help`, `loom video --help`, `loom video transcript --help`. `--content` and `--description` accept `-` to read all of stdin. `--name` does **not** — passing `--name -` sets the name to the literal string `-`.

### `loom video` — read

| Command | Returns | `--save-dir` file |
|---|---|---|
| `video list [--limit N] [--all]` | Your videos, most recent first | |
| `video search QUERY [--limit N] [--all]` | Videos matching a keyword | |
| `video get VIDEO_ID` | Metadata: name, duration, owner, views, created date | `metadata.json` |
| `video details VIDEO_ID` | Metadata + transcript + chapters + summary + tasks + comments, concurrently, as markdown | `details.md`, `metadata.json`, `transcript.txt`, `chapters.txt`, `summary.txt`, `tasks.txt`, `comments.txt` |
| `video transcript VIDEO_ID` | Full transcript with timestamps and speakers | `transcript.txt` |
| `video captions VIDEO_ID` | WebVTT captions with start+end times per cue | `captions.vtt` |
| `video summary VIDEO_ID` | AI-generated summary | `summary.txt` |
| `video chapters VIDEO_ID` | AI-generated chapter markers | `chapters.txt` |
| `video takeaways VIDEO_ID` | AI-generated key takeaways | `takeaways.txt` |
| `video description VIDEO_ID` | AI description with timestamped sections | `description.txt` |
| `video tags VIDEO_ID` | Tags on the video | `tags.txt` |
| `video comments VIDEO_ID` | Comments and threaded replies | `comments.txt` |
| `video tasks VIDEO_ID` | AI-extracted action items | `tasks.txt` |
| `video reactions VIDEO_ID` | Emoji reactions, with who and when | `reactions.txt` |
| `video backlinks VIDEO_ID` | Where the video is shared or embedded | `backlinks.txt` |
| `video confluence VIDEO_ID` | Linked Confluence pages | |
| `video meeting-notes VIDEO_ID` | Confluence meeting notes URL | |
| `video download-url VIDEO_ID` | Signed MP4 download URL | |
| `video watch-time VIDEO_ID` | Last timestamp where you stopped watching | |

`--limit N` takes 1–200 and defaults to 50. `--all` drains every page instead and ignores `--limit`.

### `loom video` — write

| Command | Effect |
|---|---|
| `video rename VIDEO_ID --name TEXT` | Rename a video |
| `video set-description VIDEO_ID --description TEXT\|-` | Overwrite the description |
| `video settings VIDEO_ID --set KEY=VALUE` | Update settings; repeatable, `VALUE` is JSON-decoded when possible |
| `video delete VIDEO_ID` | Permanently delete a video — cannot be undone |
| `video archive VIDEO_ID... [--archive\|--no-archive]` | Archive (default) or unarchive videos |
| `video recover VIDEO_ID` | Recover a deleted video from the trash |
| `video duplicate VIDEO_ID` | Duplicate a video |
| `video pin VIDEO_ID [--pin\|--no-pin]` | Pin or unpin a video in your library |
| `video follow VIDEO_ID [--follow\|--no-follow]` | Follow or unfollow a video |
| `video move VIDEO_ID... --to FOLDER_ID` | Move videos into a folder |
| `video share VIDEO_ID... --space SPACE_ID` | Share to one or more spaces (repeat `--space`) |
| `video regenerate-mp4 VIDEO_ID` | Trigger MP4 regeneration |

### `loom comment`

| Command | R/W | Effect |
|---|---|---|
| `comment reactions COMMENT_ID [--type COMMENT\|REPLY]` | R | Emoji reactions on a comment |
| `comment add VIDEO_ID --content TEXT\|- [--timestamp N]` | W | Post a comment, optionally at a timestamp (seconds) |
| `comment edit COMMENT_ID --video VIDEO_ID --content TEXT\|-` | W | Overwrite a comment's text |
| `comment delete COMMENT_ID [--type COMMENT\|REPLY]` | W | Delete a comment — cannot be undone |
| `comment react COMMENT_ID --reaction EMOJI [--type COMMENT\|REPLY]` | W | React to a comment |

### `loom task` — AI-extracted action items

| Command | R/W | Effect |
|---|---|---|
| `task add VIDEO_ID --content TEXT\|- [--timestamp N]` | W | Create an action item |
| `task update TASK_ID --content TEXT\|-` | W | Update an action item's text |
| `task delete TASK_ID` | W | Delete an action item — cannot be undone |
| `task approve TASK_ID` | W | Mark an action item approved |
| `task respond TASK_ID [--responded\|--no-responded]` | W | Mark an action item responded (or not) |

Reading tasks is `loom video tasks VIDEO_ID` — the `task` group is writes only.

### `loom reaction`

| Command | R/W | Effect |
|---|---|---|
| `reaction frequent` | R | Your most-used emoji reaction types |
| `reaction add VIDEO_ID --time N --type TYPE` | W | React to a video at a timestamp |
| `reaction delete REACTION_ID` | W | Delete a reaction |

### `loom folder`

| Command | R/W | Effect |
|---|---|---|
| `folder list [--limit N] [--all]` | R | Your folders, most recent first |
| `folder search QUERY` | R | Search folders by name |
| `folder get FOLDER_ID` | R | Folder details: name, visibility, creator |
| `folder create --name TEXT` | W | Create a folder |
| `folder rename FOLDER_ID --name TEXT` | W | Rename a folder |
| `folder delete FOLDER_ID...` | W | Delete folders — cannot be undone |
| `folder move FOLDER_ID... --to FOLDER_ID` | W | Move folders into a parent folder |

### `loom space`, `watch-later`, `tag`, `user`

| Command | R/W | Effect |
|---|---|---|
| `space list [--all\|--no-all]` | R | Spaces you belong to; drains all pages by default |
| `space get SPACE_ID` | R | Space details |
| `watch-later count` | R | How many videos are in Watch Later |
| `watch-later add VIDEO_ID [--minutes-from-utc N]` | W | Add a video to Watch Later |
| `watch-later remove VIDEO_ID` | W | Remove a video from Watch Later |
| `tag search QUERY` | R | Search workspace tags |
| `tag follow TAG [--follow\|--no-follow]` | W | Follow or unfollow a tag |
| `user get USER_ID` | R | A Loom user profile |
| `user video-count USER_ID` | R | Total videos for a user |

`space list` drains every page by default; `--limit` only takes effect together with `--no-all`. `tag search` is known to return rows containing little more than a type marker — the upstream GraphQL selection set is thin. Prefer `video tags VIDEO_ID` when you want the tags actually on a video.

## Workflows

### "Summarize this loom" / "what did they say in this loom?"

Given a pasted URL, extract the ID and read the AI summary first — it is one small call and usually answers the question.

```bash
VIDEO_ID=$(loom_id "$URL")
$LOOM video summary "$VIDEO_ID"
```

If the summary is `null` (Loom never generated one) or the user wants specifics — a quote, a decision, who said what — fall back to the transcript. Transcripts are long, so write to a file rather than flooding the conversation, then `Read` it:

```bash
$LOOM video transcript "$VIDEO_ID" -o /tmp/loom-$VIDEO_ID.txt
```

When the user wants a real briefing rather than a one-liner, `video details` fetches metadata, transcript, chapters, summary, tasks and comments **concurrently** and renders one markdown document — one call instead of six:

```bash
$LOOM video details "$VIDEO_ID" --save-dir ./notes
```

That writes `./notes/<VIDEO_ID>/details.md` plus each fetched artifact (`metadata.json`, `transcript.txt`, `chapters.txt`, `summary.txt`, `tasks.txt`, `comments.txt`), so you can `Read` just the piece you need. `details` does not cover takeaways, captions, description, tags, reactions or backlinks — run those commands separately if you need them.

### "Extract action items across my last 10 looms"

List the IDs as JSON, then pull each video's AI-extracted tasks. `video tasks` is list-shaped, so it prints `[]` (never `null`) and the loop is safe:

```bash
$LOOM video list --limit 10 --json | jq -r '.[].id' | while read -r id; do
  name=$($LOOM video get "$id" --json | jq -r '.name')
  echo "## $name ($id)"
  $LOOM video tasks "$id" --json | jq -r '.[] | "- \(.content)"'
done
```

Collect the output, then synthesize into a single grouped to-do list for the user. If a video has no AI tasks, mine `video takeaways` or the transcript for commitments instead of reporting nothing.

### "Find the loom where we discussed X"

```bash
$LOOM video search "pricing model" --limit 20 --json | jq -r '.[] | "\(.id)\t\(.name)"'
```

Search matches video metadata, not transcript bodies. When the user is sure the phrase was *spoken*, search is the wrong tool: narrow by date with `video list`, then grep transcripts.

```bash
$LOOM video list --limit 25 --json | jq -r '.[].id' | while read -r id; do
  $LOOM video transcript "$id" -q | grep -qi "pricing model" && echo "hit: $id"
done
```

That is one API call per video — tell the user the scope before running it over a large library.

### "Download this Loom"

```bash
$LOOM video download-url "$VIDEO_ID"
```

If it prints `null`, the MP4 has not been rendered yet. Trigger a render, wait, and ask again:

```bash
$LOOM video regenerate-mp4 "$VIDEO_ID"
sleep 30
$LOOM video download-url "$VIDEO_ID"
```

The result is a signed URL. **Ask the user before actually downloading the file** — hand them the URL and let them confirm, rather than pulling a large binary unprompted.

### "Turn this loom into meeting notes"

```bash
$LOOM video details "$VIDEO_ID" --save-dir ./notes
```

Then `Read` `./notes/<VIDEO_ID>/details.md` and write the notes yourself. Do not post anything back to Loom unless asked.

### Writes and destructive commands

Everything in the W rows changes the user's Loom account, and `delete` on videos, comments, tasks and folders **cannot be undone**. Before running any write:

1. Confirm the exact operation with the user in chat and wait for a clear yes.
2. Dry-run it first — every write command accepts `--dry-run` and prints the resolved operation without calling Loom.

```bash
$LOOM video delete "$VIDEO_ID" --dry-run
$LOOM comment add "$VIDEO_ID" --content "Nice walkthrough" --timestamp 42 --dry-run
```

Posting a comment or a task is a message sent on the user's behalf — get explicit approval, never infer it from "handle this loom for me".

## Output handling

- **Default (human text)** — use for anything you are going to read and summarize. It is compact and already formatted.
- **`--json`** — use whenever you are going to parse, loop, filter, or pipe into `jq`. Never regex the human rendering; it is for people.
- **`-o PATH`** — use for long payloads (transcripts, captions, `video list --all`) so they land on disk instead of in the conversation. Then `Read` the file, or `grep` it, and report only what matters.
- **`--save-dir DIR`** — use with `video details` (or any video read) to get a canonical, stable filename per command under `DIR/<video_id>/`. Repeated runs overwrite in place, so a directory of videos ends up uniformly laid out.
- **`-q`** — silences the stderr notes and `[Saved to ...]` lines when you only want the payload.

Empty is not an error. List-shaped reads (comments, tasks, reactions, tags, takeaways, backlinks, confluence, search results, folder and space lists) print `[]`; scalar reads with no value (no transcript, no summary, no download URL) print `null` and explain themselves on stderr. Both exit `0` — report "this video has no summary", not "the command failed".

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success, including empty results |
| `1` | Loom API or unexpected error |
| `2` | Usage error or invalid ID |
| `3` | Auth — missing or expired session |
| `4` | Not found |
| `5` | Network, timeout, or rate limit |

Always check the exit code; the CLI writes one clean line to stderr rather than a traceback.

## Troubleshooting

**Exit `3` — expired or missing cookie.** This is the common one. Loom session cookies last about 30 days. Tell the user to re-copy `connect.sid` from DevTools (loom.com → Application → Cookies) and re-export `LOOM_COOKIE`, then retry. Do **not** try to fetch or refresh the cookie yourself, and never print the cookie value back into the conversation.

**Exit `2` on a video you know exists.** You almost certainly passed a full `loom.com` URL instead of the bare ID. Run it through `loom_id` first.

**`loom.sh: vendored CLI not found`.** The skill is installed but `vendor/` is missing, so the copy of the CLI never arrived. Reinstall the skill. If the user already has `loom` on PATH, `LOOM_BIN=loom` works around it immediately.

**Exit `4`.** The ID is well-formed but the video, folder, comment or task does not exist, or your account cannot see it. Private videos in a workspace you are not a member of look identical to deleted ones.

**Exit `5`.** Network trouble, a timeout, or Loom rate-limiting you. Retry once; if the video is very long, raise the ceiling with `--timeout 120`. Back off rather than hammering — the rate limit is on the user's own account.

**`video download-url` prints `null`.** The MP4 has not been rendered. Run `video regenerate-mp4 VIDEO_ID`, wait ~30 seconds, and retry.

**`tag search` returns near-empty rows.** Known upstream limitation — the GraphQL selection set requests almost no fields. Use `video tags VIDEO_ID` instead.

**Neither `uvx` nor `loom` found.** Install `uv` (https://docs.astral.sh/uv/). Do not shell out to `pip install` into the system Python, and do not try to install `mcp-loom` from PyPI — the published release there is the pre-2.0 MCP server, not this CLI.
