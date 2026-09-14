#!/usr/bin/env bash
# Preflight check for the loom skill.
# Verifies uv/uvx (or a loom on PATH), that the vendored CLI shipped with this
# skill is intact and runnable, that LOOM_COOKIE is set and well-formed, and
# that the session works by making one live read-only call.
# Exits 0 on success, 1 on any missing requirement. Prints a copy-paste fix
# for each problem.

set -u

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

PASS=0
FAIL=0

check() {
  local label="$1"
  local status="$2"
  local detail="${3:-}"
  local fix="${4:-}"

  if [[ "$status" == "ok" ]]; then
    printf '  %s✓%s %s%s\n' "$GREEN" "$RESET" "$label" "${detail:+ ($detail)}"
    PASS=$((PASS + 1))
  else
    printf '  %s✗%s %s%s\n' "$RED" "$RESET" "$label" "${detail:+ — $detail}"
    if [[ -n "$fix" ]]; then
      printf '    %sfix:%s %s\n' "$YELLOW" "$RESET" "$fix"
    fi
    FAIL=$((FAIL + 1))
  fi
}

skip() {
  printf '  %s-%s %s — %s\n' "$YELLOW" "$RESET" "$1" "$2"
}

printf '%sloom preflight%s\n\n' "$BOLD" "$RESET"

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd -P "$SCRIPT_DIR/.." && pwd)"

# ---------------------------------------------------------------- runner ----
# The CLI ships inside this skill (skills/loom/vendor), so there is nothing to
# install and nothing to fetch from PyPI. uvx builds that vendored copy; the
# only external requirement is uv itself.
if command -v uvx >/dev/null 2>&1; then
  check "uvx" ok "$(uvx --version 2>/dev/null | head -n1)"
elif command -v loom >/dev/null 2>&1; then
  # Not a failure: loom.sh falls back to a loom on PATH when uvx is absent.
  check "runner" ok "uvx not on PATH; loom.sh will fall back to $(command -v loom)"
  printf '    %snote:%s install uv so the vendored copy is used instead: https://docs.astral.sh/uv/getting-started/installation/\n' \
    "$YELLOW" "$RESET"
else
  check "uvx or loom" missing "neither is on PATH" \
    "Install uv: https://docs.astral.sh/uv/getting-started/installation/"
fi

# ----------------------------------------------------------- vendored cli ---
if [[ -f "$SKILL_DIR/vendor/pyproject.toml" ]]; then
  if [[ -f "$SKILL_DIR/vendor/VENDOR.json" ]] \
     && bash "$SCRIPT_DIR/sync-vendor.sh" --check >/dev/null 2>&1; then
    check "vendored CLI" ok "integrity verified"
  else
    # Present but modified or unstamped. Still runnable, so this is a warning
    # rather than a failure — it only means the copy no longer matches upstream.
    printf '  %s!%s vendored CLI — present but does not match its recorded fingerprint\n' "$YELLOW" "$RESET"
    printf '    %snote:%s vendor/ was edited by hand; re-sync with: bash %s/sync-vendor.sh /path/to/mcp-loom\n' \
      "$YELLOW" "$RESET" "$SCRIPT_DIR"
  fi
else
  check "vendored CLI" missing "no $SKILL_DIR/vendor — skill looks incompletely installed" \
    "Reinstall the skill, or set LOOM_BIN to a loom already on PATH"
fi

# Everything below drives the CLI through the wrapper, which resolves the
# vendored copy from its own location regardless of the current directory.
LOOM="bash $SCRIPT_DIR/loom.sh"

# ------------------------------------------------------------------ cli -----
CLI_OK=0
if VERSION_OUT=$($LOOM --version 2>&1); then
  check "loom CLI" ok "$(printf '%s' "$VERSION_OUT" | head -n1)"
  CLI_OK=1
else
  check "loom CLI" missing "$(printf '%s' "$VERSION_OUT" | tail -n1)" \
    "Run 'bash $SCRIPT_DIR/loom.sh --version' by hand to see the full error"
fi

# ----------------------------------------------------------------- auth -----
COOKIE_OK=0
if [[ -n "${LOOM_COOKIE:-}" ]]; then
  cookie="$LOOM_COOKIE"
  # Accept both the raw connect.sid value and a full 'connect.sid=...' pair.
  bare="${cookie#connect.sid=}"
  if [[ "$bare" == s%3A* || "$bare" == s:* ]]; then
    check "LOOM_COOKIE" ok "${bare:0:8}…${bare: -4}"
    COOKIE_OK=1
  else
    check "LOOM_COOKIE" invalid "set but doesn't look like a connect.sid value (expected it to start with s%3A)" \
      "Copy the VALUE of the connect.sid cookie from loom.com (DevTools → Application → Cookies), then: export LOOM_COOKIE='s%3A...'"
  fi
elif [[ -n "${LOOM_AUTH_FILE:-}" ]]; then
  if [[ -r "$LOOM_AUTH_FILE" ]]; then
    check "LOOM_AUTH_FILE" ok "$LOOM_AUTH_FILE"
    COOKIE_OK=1
  else
    check "LOOM_AUTH_FILE" missing "set to $LOOM_AUTH_FILE but that file is not readable" \
      "Point LOOM_AUTH_FILE at a Playwright storage-state JSON file, or use LOOM_COOKIE instead"
  fi
else
  check "LOOM_COOKIE" missing "not set in env" \
    "Sign in at https://www.loom.com, then DevTools → Application → Cookies → copy the connect.sid VALUE → export LOOM_COOKIE='s%3A...'"
fi

# ------------------------------------------------------------ live call -----
# One read-only call, capped at a single row. `video list` is used deliberately:
# it is the cheapest read that actually authenticates. `reaction frequent` is a
# lighter-looking probe but returns a plausible list even when the session cookie
# is dead, so it cannot tell a live session from an expired one.
if [[ $CLI_OK -eq 1 && $COOKIE_OK -eq 1 ]]; then
  LIVE_OUT=$($LOOM video list --limit 1 -q 2>&1)
  LIVE_CODE=$?
  case "$LIVE_CODE" in
    0)
      check "live session" ok "video list → $(printf '%s' "$LIVE_OUT" | head -n1 | cut -c1-48)"
      ;;
    3)
      check "live session" failed "Loom rejected the session (exit 3 — cookie missing or expired)" \
        "Session cookies last ~30 days. Re-copy connect.sid from loom.com and re-export LOOM_COOKIE."
      ;;
    5)
      check "live session" failed "network error, timeout, or rate limit (exit 5)" \
        "Check connectivity and retry; for slow links add --timeout 120"
      ;;
    *)
      check "live session" failed "exit $LIVE_CODE — $(printf '%s' "$LIVE_OUT" | tail -n1)" \
        "Run '$LOOM video list --limit 1' by hand to see the full error"
      ;;
  esac
else
  skip "live session" "skipped (needs a working CLI and credentials)"
fi

printf '\n'

if [[ $FAIL -eq 0 ]]; then
  printf '%sAll checks passed.%s Ready to read Loom videos.\n' "$GREEN" "$RESET"
  exit 0
else
  printf '%s%d check(s) failed.%s Fix the items above and re-run this script.\n' "$RED" "$FAIL" "$RESET"
  exit 1
fi
