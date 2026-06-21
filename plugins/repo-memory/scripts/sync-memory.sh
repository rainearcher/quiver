#!/usr/bin/env bash
# repo-memory :: Stop
# Commit memory-only changes onto the target branch (default: main) and push,
# WITHOUT touching the user's current branch, index, or working tree.
# Uses a throwaway index + commit-tree so the commit is always memory-only and
# always lands on the target branch regardless of which branch is checked out.
# Always exits 0.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$DIR/lib.sh"

main() {
  local cwd root
  cwd="$(rm_cwd)"
  root="$(rm_main_root "$cwd")"
  [ -z "$root" ] && return 0
  rm_load_config "$root"
  [ "$RM_AUTOPUSH" = "true" ] || { rm_log "$root" "autopush disabled; skip"; return 0; }
  git -C "$root" rev-parse --git-dir >/dev/null 2>&1 || return 0

  # Nothing staged-or-unstaged under the memory dir vs HEAD AND vs remote? still
  # proceed (remote may differ), but if working tree has no memory at all, bail.
  [ -d "$root/$RM_SUBDIR" ] || return 0

  local tries=0 base base_tree tmpidx tree commit cur
  while [ "$tries" -lt 3 ]; do
    tries=$((tries+1))
    git -C "$root" fetch -q "$RM_REMOTE" "$RM_BRANCH" 2>/dev/null || { rm_log "$root" "fetch failed"; return 0; }
    base="$(git -C "$root" rev-parse FETCH_HEAD 2>/dev/null)"
    [ -z "$base" ] && return 0
    base_tree="$(git -C "$root" rev-parse "$base^{tree}" 2>/dev/null)"

    tmpidx="$(mktemp)"
    (
      export GIT_INDEX_FILE="$tmpidx"
      cd "$root" || exit 1
      git read-tree "$base" 2>/dev/null || exit 1
      # --ignore-removal: stage additions + modifications only, never deletions.
      # This makes sync an additive union on top of the remote tip, so another
      # machine's memory files are never clobbered by this checkout being behind.
      git add --ignore-removal -- "$RM_SUBDIR" 2>/dev/null || exit 1
    ) || { rm -f "$tmpidx"; rm_log "$root" "index build failed"; return 0; }

    tree="$(GIT_INDEX_FILE="$tmpidx" git -C "$root" write-tree 2>/dev/null)"
    rm -f "$tmpidx"
    [ -z "$tree" ] && return 0

    if [ "$tree" = "$base_tree" ]; then
      rm_log "$root" "no memory changes to sync"
      return 0
    fi

    commit="$(printf 'chore(memory): sync from %s\n' "$(hostname 2>/dev/null || echo host)" \
      | git -C "$root" commit-tree "$tree" -p "$base" 2>/dev/null)"
    [ -z "$commit" ] && return 0

    if git -C "$root" push -q "$RM_REMOTE" "$commit:refs/heads/$RM_BRANCH" 2>/dev/null; then
      rm_log "$root" "pushed memory commit $commit -> $RM_REMOTE/$RM_BRANCH"
      # Fast-forward the local branch ref too, but only when it's not the
      # checked-out branch (avoids desyncing HEAD/index) and only if it still
      # points at the base we built on (no-op otherwise).
      cur="$(git -C "$root" symbolic-ref --short -q HEAD 2>/dev/null)"
      if [ "$cur" != "$RM_BRANCH" ]; then
        git -C "$root" update-ref "refs/heads/$RM_BRANCH" "$commit" "$base" 2>/dev/null || true
      fi
      return 0
    fi
    rm_log "$root" "push race (try $tries); refetching"
  done
  rm_log "$root" "push failed after retries"
  return 0
}

main || true
exit 0
