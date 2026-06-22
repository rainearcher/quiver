#!/usr/bin/env bash
# repo-memory shared helpers. Sourced by session-start.sh and sync-memory.sh.
#
# Design notes (verified against Claude Code 2.1.185):
#  - autoMemoryDirectory only honors ABSOLUTE paths; relative paths are ignored.
#  - We therefore compute an absolute path at runtime and write it into the
#    current working dir's .claude/settings.local.json (gitignored, per-checkout).
#  - The canonical memory dir is anchored to the MAIN worktree so every git
#    worktree on a machine shares ONE memory dir instead of fragmenting.
#  - Hooks must never break a session: every entrypoint exits 0 and logs.

set -uo pipefail

# ---- read the hook stdin payload once (JSON) -------------------------------
RM_STDIN="$(cat 2>/dev/null || true)"

rm_json() {
  # rm_json <jq-ish key path via python> -- extract a string field from stdin JSON
  local key="$1"
  printf '%s' "$RM_STDIN" | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    print(''); sys.exit(0)
v=d
for k in '$key'.split('.'):
    if isinstance(v,dict): v=v.get(k)
    else: v=None
print(v if isinstance(v,str) else '')
" 2>/dev/null
}

# ---- resolve the project cwd ----------------------------------------------
rm_cwd() {
  local c
  c="$(rm_json cwd)"
  [ -z "$c" ] && c="${CLAUDE_PROJECT_DIR:-$PWD}"
  printf '%s' "$c"
}

# ---- config (env > .claude/repo-memory.json > defaults) --------------------
# Resolves: RM_SUBDIR, RM_REMOTE, RM_BRANCH, RM_AUTOPUSH
rm_load_config() {
  local root="$1"
  RM_SUBDIR="${REPO_MEMORY_SUBDIR:-}"
  RM_REMOTE="${REPO_MEMORY_REMOTE:-}"
  RM_BRANCH="${REPO_MEMORY_BRANCH:-}"
  RM_AUTOPUSH="${REPO_MEMORY_AUTOPUSH:-}"
  local cfg="$root/.claude/repo-memory.json"
  if [ -f "$cfg" ]; then
    eval "$(python3 -c "
import json
try: d=json.load(open('$cfg'))
except Exception: d={}
def emit(k,v):
    if v is None: return
    print('%s=%s'%(k, json.dumps(str(v))))
if not '${RM_SUBDIR}': emit('RM_SUBDIR', d.get('memoryDir'))
if not '${RM_REMOTE}': emit('RM_REMOTE', d.get('remote'))
if not '${RM_BRANCH}': emit('RM_BRANCH', d.get('branch'))
if '${RM_AUTOPUSH}'=='' and d.get('autoPush') is not None:
    emit('RM_AUTOPUSH', 'true' if d.get('autoPush') else 'false')
" 2>/dev/null)"
  fi
  : "${RM_SUBDIR:=.claude/memory}"
  : "${RM_REMOTE:=origin}"
  : "${RM_BRANCH:=main}"
  : "${RM_AUTOPUSH:=true}"
}

# ---- locate the canonical (main-worktree) repo root ------------------------
# Echoes the absolute main worktree root, or empty if not a git repo.
rm_main_root() {
  local cwd="$1" common
  common="$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || return 0
  [ -z "$common" ] && return 0
  # common dir is "<mainroot>/.git" for normal repos (shared by all worktrees)
  dirname "$common"
}

# ---- logging ---------------------------------------------------------------
rm_log() {
  local root="${1:-}"; shift || true
  local line; line="$(date -u +%FT%TZ) $*"
  if [ -n "$root" ] && [ -d "$root/.claude" ]; then
    printf '%s\n' "$line" >> "$root/.claude/repo-memory.log" 2>/dev/null || true
  fi
}

# ---- write the memory settings into a JSON settings file (no clobber) ------
# Sets autoMemoryDirectory (absolute string) AND autoMemoryEnabled:true (bool).
# autoMemoryEnabled defaults OFF in headless `-p` mode, so it must be explicit
# for runners/cron jobs to inject memory. Merges into existing settings.
rm_apply_memory_settings() {
  local file="$1" dir="$2"
  mkdir -p "$(dirname "$file")"
  python3 -c "
import json,os,sys
f='$file'; d='$dir'
try:
    cur=json.load(open(f)) if os.path.exists(f) and os.path.getsize(f) else {}
    if not isinstance(cur,dict): cur={}
except Exception:
    cur={}
if cur.get('autoMemoryDirectory')==d and cur.get('autoMemoryEnabled') is True:
    sys.exit(0)            # already correct, leave mtime alone
cur['autoMemoryDirectory']=d
cur['autoMemoryEnabled']=True
json.dump(cur,open(f,'w'),indent=2)
open(f,'a').write('\n')
" 2>/dev/null
}
