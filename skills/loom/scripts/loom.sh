#!/usr/bin/env bash
# Run the vendored `loom` CLI that ships inside this skill.
#
# The skill is installed to a different path depending on how you got it
# (~/.claude/plugins/marketplaces/quiver/skills/loom, ~/.claude/skills/loom,
# .claude/skills/loom inside a project, ...), and CLAUDE_PLUGIN_ROOT is not set
# for plain Bash calls. So this script locates itself instead of being told
# where it is: BASH_SOURCE always resolves, however it was invoked.
#
# Usage:  bash <path-to-this-script> video transcript VIDEO_ID
#
# Set LOOM_BIN to bypass the vendored copy entirely:
#   LOOM_BIN=loom bash scripts/loom.sh --version

set -euo pipefail

source_path="${BASH_SOURCE[0]}"
# Resolve symlinks so `ln -s` into a bin dir still finds the vendor tree.
while [ -L "$source_path" ]; do
  link_target="$(readlink "$source_path")"
  case "$link_target" in
    /*) source_path="$link_target" ;;
    *) source_path="$(cd -P "$(dirname "$source_path")" && pwd)/$link_target" ;;
  esac
done
script_dir="$(cd -P "$(dirname "$source_path")" && pwd)"
skill_dir="$(cd -P "$script_dir/.." && pwd)"
vendor_dir="$skill_dir/vendor"

# An explicit override wins over everything else.
if [ -n "${LOOM_BIN:-}" ]; then
  exec "$LOOM_BIN" "$@"
fi

if [ ! -f "$vendor_dir/pyproject.toml" ]; then
  echo "loom.sh: vendored CLI not found at $vendor_dir" >&2
  echo "  The skill looks incompletely installed. Reinstall it, or set LOOM_BIN to a loom on PATH." >&2
  exit 70
fi

if ! command -v uvx >/dev/null 2>&1; then
  # No uv, but the user may have installed the CLI themselves.
  if command -v loom >/dev/null 2>&1; then
    exec loom "$@"
  fi
  echo "loom.sh: uvx not found and no 'loom' on PATH." >&2
  echo "  Install uv: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 70
fi

# --from <dir> builds the vendored package once and caches the result; later
# calls are ~0.1s. --quiet keeps uv's resolver chatter off the CLI's stderr,
# which the skill treats as meaningful output.
exec uvx --quiet --from "$vendor_dir" loom "$@"
