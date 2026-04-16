#!/usr/bin/env bash
# Preflight check for perplexity-research.
# Verifies curl, jq, and PERPLEXITY_API_KEY are ready. Exits 0 on success,
# 1 on any missing requirement. Prints a copy-paste fix for each problem.

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

printf '%sperplexity-research preflight%s\n\n' "$BOLD" "$RESET"

if command -v curl >/dev/null 2>&1; then
  check "curl" ok "$(curl --version | head -n1 | awk '{print $1" "$2}')"
else
  check "curl" missing "not on PATH" "macOS: brew install curl | Debian/Ubuntu: sudo apt install curl | Alpine: apk add curl"
fi

if command -v jq >/dev/null 2>&1; then
  check "jq" ok "$(jq --version)"
else
  check "jq" missing "not on PATH" "macOS: brew install jq | Debian/Ubuntu: sudo apt install jq | Alpine: apk add jq"
fi

if [[ -n "${PERPLEXITY_API_KEY:-}" ]]; then
  key="$PERPLEXITY_API_KEY"
  if [[ "$key" == pplx-* && ${#key} -ge 20 ]]; then
    masked="${key:0:8}…${key: -4}"
    check "PERPLEXITY_API_KEY" ok "$masked"
  else
    check "PERPLEXITY_API_KEY" invalid "set but doesn't look like a Perplexity key (expected pplx-…)" \
      "Create a key at https://www.perplexity.ai/account/api and re-export it"
  fi
else
  check "PERPLEXITY_API_KEY" missing "not set in env" \
    "export PERPLEXITY_API_KEY=pplx-...  (get a key at https://www.perplexity.ai/account/api)"
fi

printf '\n'

if [[ $FAIL -eq 0 ]]; then
  printf '%sAll checks passed.%s Ready to run deep research.\n' "$GREEN" "$RESET"
  exit 0
else
  printf '%s%d check(s) failed.%s Fix the items above and re-run this script.\n' "$RED" "$FAIL" "$RESET"
  exit 1
fi
