#!/usr/bin/env bash
# repo-memory :: SessionStart
# 1. Point autoMemoryDirectory at the canonical (main-worktree) memory dir.
# 2. Pull the latest memory from the configured remote/branch.
# Always exits 0 so it can never block a session.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$DIR/lib.sh"

main() {
  local cwd root memdir
  cwd="$(rm_cwd)"
  root="$(rm_main_root "$cwd")"
  [ -z "$root" ] && return 0          # not a git repo: nothing to do
  rm_load_config "$root"

  memdir="$root/$RM_SUBDIR"
  mkdir -p "$memdir" 2>/dev/null || true

  # (1) Redirect this checkout's memory at the canonical dir and enable memory.
  # Written to the CURRENT cwd's local settings so worktrees self-configure, all
  # pointing at the one shared (main-worktree) memory dir. Absolute path is
  # required, and autoMemoryEnabled must be explicit for headless `-p` jobs.
  # NOTE: the memory directory is resolved BEFORE SessionStart hooks run, so a
  # hook-written path only takes effect from the NEXT session. On persistent
  # machines run setup.sh once (it pre-writes this) so session 1 also works;
  # ephemeral single-session clones must set it in their bootstrap.
  rm_apply_memory_settings "$cwd/.claude/settings.local.json" "$memdir"

  # (2) Pull latest memory (memory subtree only) BEFORE creating any stub, so a
  # freshly created index file can't mark the tree dirty and block the pull.
  # Skip only if TRACKED memory files have local modifications (Stop pushes
  # those). Untracked local facts are preserved — checkout is additive.
  if git -C "$root" rev-parse --git-dir >/dev/null 2>&1; then
    if git -C "$root" fetch -q "$RM_REMOTE" "$RM_BRANCH" 2>/dev/null \
       && git -C "$root" cat-file -e "FETCH_HEAD:$RM_SUBDIR" 2>/dev/null; then
      if git -C "$root" diff --quiet -- "$RM_SUBDIR" 2>/dev/null \
         && git -C "$root" diff --cached --quiet -- "$RM_SUBDIR" 2>/dev/null; then
        git -C "$root" checkout -q FETCH_HEAD -- "$RM_SUBDIR" 2>/dev/null \
          && rm_log "$root" "pulled memory from $RM_REMOTE/$RM_BRANCH"
      else
        rm_log "$root" "skipped pull: tracked memory has local modifications"
      fi
    fi
  fi

  # (3) Only now ensure an index file exists (after a pull may have provided it).
  if [ ! -f "$memdir/MEMORY.md" ]; then
    printf '# Memory Index\n\n_(repo-memory: project memory lives here and syncs via git)_\n' \
      > "$memdir/MEMORY.md" 2>/dev/null || true
  fi

  return 0
}

main || true
exit 0
