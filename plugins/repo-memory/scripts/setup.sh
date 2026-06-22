#!/usr/bin/env bash
# repo-memory :: one-time per-repo setup
# Migrates any existing machine-local project memory into the repo and makes
# the working tree ready for git-synced memory. Safe to re-run (idempotent).
#
# Usage:  bash setup.sh [repo-root]   (defaults to current git repo root)

set -uo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
SUBDIR="${REPO_MEMORY_SUBDIR:-.claude/memory}"
TARGET="$ROOT/$SUBDIR"

slugify() { printf '%s' "$1" | sed 's/[/.]/-/g'; }
DEFAULT_DIR="$HOME/.claude/projects/$(slugify "$ROOT")/memory"

echo "repo-memory setup"
echo "  repo root   : $ROOT"
echo "  memory dir  : $TARGET"
echo "  legacy dir  : $DEFAULT_DIR"

mkdir -p "$TARGET"

migrated=0
if [ -d "$DEFAULT_DIR" ]; then
  shopt -s dotglob nullglob
  for f in "$DEFAULT_DIR"/*; do
    base="$(basename "$f")"
    if [ ! -e "$TARGET/$base" ]; then
      cp -a "$f" "$TARGET/$base" && migrated=$((migrated+1))
    fi
  done
  shopt -u dotglob nullglob
fi
echo "  migrated    : $migrated file(s) from legacy dir"

if [ ! -f "$TARGET/MEMORY.md" ]; then
  printf '# Memory Index\n\n_(repo-memory: project memory lives here and syncs via git)_\n' > "$TARGET/MEMORY.md"
  echo "  created MEMORY.md stub"
fi

# Pre-write the per-machine local setting so memory injects from session 1.
# (The directory is resolved before SessionStart hooks run, so the hook alone
# would only take effect from the 2nd session — pre-writing fixes session 1.)
python3 - "$ROOT/.claude/settings.local.json" "$TARGET" <<'PY'
import json,os,sys
f,d=sys.argv[1],sys.argv[2]
os.makedirs(os.path.dirname(f),exist_ok=True)
try:
    cur=json.load(open(f)) if os.path.exists(f) and os.path.getsize(f) else {}
    if not isinstance(cur,dict): cur={}
except Exception:
    cur={}
cur['autoMemoryDirectory']=os.path.abspath(d)
cur['autoMemoryEnabled']=True
json.dump(cur,open(f,'w'),indent=2); open(f,'a').write('\n')
print("  wrote settings.local.json -> autoMemoryDirectory=%s"%os.path.abspath(d))
PY

# Keep per-machine + runtime files out of git.
GI="$ROOT/.gitignore"
touch "$GI"
for line in ".claude/settings.local.json" ".claude/repo-memory.log"; do
  grep -qxF "$line" "$GI" 2>/dev/null || { printf '%s\n' "$line" >> "$GI"; echo "  gitignore + $line"; }
done

cat <<EOF

Next:
  1. Review & commit the migrated memory:
       git add $SUBDIR .gitignore && git commit -m "chore: adopt repo-memory" && git push
  2. Install the plugin on every machine that runs Claude here:
       /plugin marketplace add rainearcher/quiver
       /plugin install repo-memory@quiver
  3. Commit "autoMemoryEnabled": true into the repo's .claude/settings.json so
     headless ("claude -p") runners inject memory too — it defaults OFF in -p.
  4. Ephemeral single-session runners (fresh clone each run): have the bootstrap
     write .claude/settings.local.json with an ABSOLUTE autoMemoryDirectory
     BEFORE launching claude — the dir is resolved before SessionStart hooks, so
     a hook can't set it in time for that same session.
  5. (optional) Per-repo config at .claude/repo-memory.json:
       { "memoryDir": ".claude/memory", "remote": "origin", "branch": "main", "autoPush": true }

The SessionStart hook will redirect autoMemoryDirectory here automatically each
session (worktrees included); the Stop hook commits memory changes to the
target branch and pushes.
EOF
