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

### Why it's correct (verified against Claude Code 2.1.185)

- `autoMemoryDirectory` only honors **absolute** paths (relative paths are
  silently ignored), so the hook computes an absolute path at runtime and writes
  it to the checkout's `.claude/settings.local.json` (gitignored, per-machine).
- The path is anchored to the **main worktree** (via `git --git-common-dir`), so
  every `git worktree` on a machine shares **one** memory dir instead of
  fragmenting per worktree.
- A SessionStart hook runs **before** memory is loaded, so the redirect takes
  effect in the *same* session — fresh worktrees and ephemeral clones
  self-configure on first run.
- Everything runs in headless (`-p`) mode without an interactive trust dialog.

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
