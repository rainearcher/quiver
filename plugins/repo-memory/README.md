# repo-memory

Keep Claude Code's project-scoped **auto-memory inside your git repo** and sync it
across every machine that works on the project — laptop, cloud runners, ops boxes.

By default Claude stores project memory machine-locally under
`~/.claude/projects/<sanitized-cwd>/memory/`, so memory written on one machine is
invisible to every other. This plugin makes the repo itself the source of truth:
memory files live at `.claude/memory/` (committed) and travel via git.

## How it works

Two hooks, no symlinks, no daemon:

- **SessionStart** — points `autoMemoryDirectory` at the repo's canonical memory
  dir and pulls the latest copy from the remote.
- **Stop** — commits memory-only changes onto the target branch (default `main`)
  and pushes, without touching your current branch, index, or working tree.

### Verified behavior (Claude Code 2.1.185) — read before relying on this

Established with confound-free tests (markers in a directory the model cannot
browse, file-reads forbidden):

- **`autoMemoryEnabled` defaults OFF in headless `-p` mode.** Memory is only
  injected when it is explicitly `true`. Commit `"autoMemoryEnabled": true` into
  the repo's `.claude/settings.json`; the hook/setup also set it in local
  settings.
- **`autoMemoryDirectory` only honors ABSOLUTE paths** — relative paths are
  ignored. The hook computes an absolute path at runtime and writes it to
  `.claude/settings.local.json` (gitignored, per-machine).
- **The memory directory is resolved BEFORE SessionStart hooks run.** So a
  hook-written path only takes effect from the **next** session. Consequences:
  - *Persistent machines* (laptop, ops box): run `setup.sh` once — it pre-writes
    the absolute path so session 1 injects; the hook keeps it fresh after.
  - *Ephemeral single-session runners* (fresh clone each run): the bootstrap
    **must** write `settings.local.json` with the absolute path before launching
    `claude`. A hook cannot do it in time. (The committed memory files are still
    readable by the agent, and the sync hooks still run.)
- The path is anchored to the **main worktree** (via `git --git-common-dir`), so
  every `git worktree` on a machine shares **one** memory dir.
- Hooks (sync) run fine in headless `-p` mode without an interactive trust dialog.

## Install

```
/plugin marketplace add rainearcher/quiver
/plugin install repo-memory@quiver
```

Then, once per repo:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh"   # migrates existing memory + gitignore
git add .claude/memory .gitignore && git commit -m "chore: adopt repo-memory" && git push
```

Install the plugin on every machine that runs Claude in that repo.

## Configuration

Optional per-repo file `.claude/repo-memory.json` (committed):

```json
{ "memoryDir": ".claude/memory", "remote": "origin", "branch": "main", "autoPush": true }
```

Or environment variables (take precedence): `REPO_MEMORY_SUBDIR`,
`REPO_MEMORY_REMOTE`, `REPO_MEMORY_BRANCH`, `REPO_MEMORY_AUTOPUSH`.

Set `autoPush` to `false` for pull-only / read-replica behavior (memory is pulled
on session start; writes stay uncommitted for you to handle).

## Notes & trade-offs

- Memory commits land directly on the target branch as small `chore(memory):`
  commits, independent of whatever feature branch you're on — so memory stays
  fresh everywhere without waiting for merges.
- Concurrency: memory is one-fact-per-file, which merges cleanly. The push uses a
  fast-forward with retry; in the rare case two machines write the same file in
  overlapping sessions, last-writer-wins and the prior value remains in git
  history.
- Hooks never block a session: every entrypoint exits 0 and logs to
  `.claude/repo-memory.log` (gitignored).

## License

MIT
