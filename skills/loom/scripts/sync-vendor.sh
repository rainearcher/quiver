#!/usr/bin/env bash
# Sync skills/loom/vendor/ from an mcp-loom checkout, or check it for drift.
#
# The skill ships its own copy of the loom CLI so it works with nothing
# installed and nothing published to PyPI. The cost of vendoring is that the
# copy can silently fall behind upstream — this script is what stops that.
#
#   sync-vendor.sh --check            verify the vendor tree matches its recorded hash
#   sync-vendor.sh <path-to-mcp-loom> re-vendor from a local checkout
#
# Exit codes: 0 clean/synced, 1 drift detected, 2 usage error.

set -euo pipefail

script_dir="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd -P "$script_dir/.." && pwd)"
vendor_dir="$skill_dir/vendor"
stamp="$vendor_dir/VENDOR.json"

# Hash the functional surface only: the Python sources and the build metadata.
# README/LICENSE are copied verbatim but excluded, so a docs-only edit upstream
# does not show up as a false drift alarm.
fingerprint() {
  local root="$1"
  {
    find "$root/src" -name '*.py' -type f 2>/dev/null | sort | while read -r f; do
      printf '%s ' "${f#"$root"/}"
      sha256sum "$f" | cut -d' ' -f1
    done
    printf 'pyproject.toml '
    sha256sum "$root/pyproject.toml" | cut -d' ' -f1
  } | sha256sum | cut -d' ' -f1
}

usage() {
  sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 2
}

[ $# -eq 1 ] || usage

if [ "$1" = "--check" ]; then
  if [ ! -f "$stamp" ]; then
    echo "✗ no $stamp — vendor tree has never been stamped; run: sync-vendor.sh <path-to-mcp-loom>" >&2
    exit 1
  fi
  recorded="$(sed -n 's/.*"fingerprint"[[:space:]]*:[[:space:]]*"\([a-f0-9]*\)".*/\1/p' "$stamp")"
  actual="$(fingerprint "$vendor_dir")"
  if [ "$recorded" = "$actual" ]; then
    echo "✓ vendor tree matches its stamp ($actual)"
    sed -n 's/.*"source_commit"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/  vendored from commit \1/p' "$stamp"
    exit 0
  fi
  echo "✗ vendor tree has drifted" >&2
  echo "  recorded: $recorded" >&2
  echo "  actual:   $actual" >&2
  echo "  Someone edited skills/loom/vendor/ by hand. Re-vendor from upstream instead:" >&2
  echo "    bash $0 /path/to/mcp-loom" >&2
  exit 1
fi

upstream="$(cd -P "$1" && pwd)"
[ -f "$upstream/pyproject.toml" ] || { echo "✗ $upstream is not an mcp-loom checkout (no pyproject.toml)" >&2; exit 2; }
grep -q 'name = "mcp-loom"' "$upstream/pyproject.toml" || { echo "✗ $upstream/pyproject.toml is not mcp-loom" >&2; exit 2; }
[ -f "$upstream/src/loom_mcp/cli.py" ] || { echo "✗ $upstream has no src/loom_mcp/cli.py — is it pre-2.0 (MCP server)?" >&2; exit 2; }

commit="$(git -C "$upstream" rev-parse HEAD 2>/dev/null || echo unknown)"
dirty=""
if ! git -C "$upstream" diff --quiet HEAD 2>/dev/null; then
  dirty=" (working tree had uncommitted changes)"
  echo "! $upstream has uncommitted changes; vendoring the working tree as-is" >&2
fi
version="$(sed -n 's/^version = "\([^"]*\)".*/\1/p' "$upstream/pyproject.toml" | head -1)"

rm -rf "$vendor_dir"
mkdir -p "$vendor_dir"
cp -r "$upstream/src" "$vendor_dir/src"
cp "$upstream/pyproject.toml" "$upstream/README.md" "$upstream/LICENSE" "$vendor_dir/"
find "$vendor_dir" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$vendor_dir" -name '*.pyc' -delete 2>/dev/null || true

cat > "$stamp" <<EOF
{
  "_comment": "Written by scripts/sync-vendor.sh. Do not edit vendor/ by hand; edit mcp-loom and re-run the sync.",
  "upstream": "https://github.com/rainearcher/mcp-loom",
  "source_commit": "$commit",
  "version": "$version",
  "fingerprint": "$(fingerprint "$vendor_dir")"
}
EOF

echo "✓ vendored mcp-loom $version from $commit$dirty"
echo "  $(find "$vendor_dir" -type f | wc -l) files, $(du -sh "$vendor_dir" | cut -f1)"
echo "  verify: bash $script_dir/loom.sh --version"
