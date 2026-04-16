#!/usr/bin/env bash
# Perplexity Agent API wrapper — multi-step deep research with citations.
# Reads PERPLEXITY_API_KEY from env, POSTs to /v1/agent, writes a markdown
# report + raw JSON. Prints the markdown path on stdout.

set -euo pipefail

PRESET="advanced-deep-research"
MAX_STEPS=10
OUTPUT_DIR=""
TOPIC=""
DOMAINS=""
RECENCY=""
INSTRUCTIONS=""
QUERY=""

usage() {
  cat <<'EOF'
Usage: research.sh [options] "your research question"

Runs Perplexity Agent API with multi-step browsing and saves a markdown report.

Options:
  --preset NAME       advanced-deep-research (default) | deep-research |
                      pro-search | fast-search
  --max-steps N       Max research steps 1-10 (default 10)
  --output DIR        Output directory (default: ./docs/research)
  --topic SLUG        Subdirectory under --output for this topic
                      (e.g. secrets-management, instagram). Created if missing.
  --domains a,b,c     Comma-separated domain filter for web search
  --recency PERIOD    day | week | month
  --instructions STR  Custom system prompt to steer the agent
  -h, --help          Show this help

Environment:
  PERPLEXITY_API_KEY  (required)

Output:
  Writes <OUTPUT_DIR>[/<TOPIC>]/<slug>-<timestamp>.md and .json
  Prints the markdown path to stdout.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --preset) PRESET="$2"; shift 2;;
    --max-steps) MAX_STEPS="$2"; shift 2;;
    --output) OUTPUT_DIR="$2"; shift 2;;
    --topic) TOPIC="$2"; shift 2;;
    --domains) DOMAINS="$2"; shift 2;;
    --recency) RECENCY="$2"; shift 2;;
    --instructions) INSTRUCTIONS="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    --*) echo "Unknown flag: $1" >&2; usage >&2; exit 2;;
    *)
      if [[ -z "$QUERY" ]]; then QUERY="$1"; else QUERY="$QUERY $1"; fi
      shift
      ;;
  esac
done

if [[ -z "$QUERY" ]]; then
  echo "Error: research query required" >&2
  usage >&2
  exit 2
fi

if [[ -z "${PERPLEXITY_API_KEY:-}" ]]; then
  echo "Error: PERPLEXITY_API_KEY not set in environment" >&2
  echo "Add it to your shell env or ~/.claude/.env, then re-run." >&2
  exit 1
fi

for cmd in curl jq; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: '$cmd' is required but not installed" >&2
    exit 1
  fi
done

OUTPUT_DIR="${OUTPUT_DIR:-./docs/research}"
if [[ -n "$TOPIC" ]]; then
  TOPIC_SLUG=$(printf '%s' "$TOPIC" \
    | tr '[:upper:]' '[:lower:]' \
    | tr -c 'a-z0-9' '-' \
    | sed -E 's/-+/-/g; s/^-+//; s/-+$//')
  if [[ -z "$TOPIC_SLUG" ]]; then
    echo "Error: --topic value reduced to empty slug" >&2
    exit 2
  fi
  OUTPUT_DIR="$OUTPUT_DIR/$TOPIC_SLUG"
fi
mkdir -p "$OUTPUT_DIR"

SLUG=$(printf '%s' "$QUERY" \
  | tr '[:upper:]' '[:lower:]' \
  | tr -c 'a-z0-9' '-' \
  | sed -E 's/-+/-/g; s/^-+//; s/-+$//' \
  | cut -c1-50)
[[ -z "$SLUG" ]] && SLUG="query"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BASE="$OUTPUT_DIR/$SLUG-$TIMESTAMP"
JSON_PATH="$BASE.json"
MD_PATH="$BASE.md"

# Build the web_search tool config, honouring optional filters
SEARCH_TOOL='{"type":"web_search","max_tokens":8000}'
if [[ -n "$DOMAINS" || -n "$RECENCY" ]]; then
  FILTERS='{}'
  if [[ -n "$DOMAINS" ]]; then
    DOMAIN_ARRAY=$(printf '%s' "$DOMAINS" \
      | jq -Rc 'split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(length > 0))')
    FILTERS=$(jq -c --argjson d "$DOMAIN_ARRAY" '. + {search_domain_filter: $d}' <<<"$FILTERS")
  fi
  if [[ -n "$RECENCY" ]]; then
    FILTERS=$(jq -c --arg r "$RECENCY" '. + {search_recency_filter: $r}' <<<"$FILTERS")
  fi
  SEARCH_TOOL=$(jq -c --argjson f "$FILTERS" '. + {filters: $f}' <<<"$SEARCH_TOOL")
fi

REQ_BODY=$(jq -n \
  --arg input "$QUERY" \
  --arg preset "$PRESET" \
  --argjson max_steps "$MAX_STEPS" \
  --argjson search_tool "$SEARCH_TOOL" \
  --arg instructions "$INSTRUCTIONS" \
  '{
    input: $input,
    preset: $preset,
    max_steps: $max_steps,
    stream: false,
    tools: [$search_tool, {type: "fetch_url", max_urls: 10}]
  }
  + (if $instructions == "" then {} else {instructions: $instructions} end)')

echo "Calling Perplexity Agent API (preset: $PRESET, max_steps: $MAX_STEPS)..." >&2
echo "Deep research queries can take 2-5 minutes. Waiting..." >&2

HTTP_CODE=$(curl -sS -w "%{http_code}" -o "$JSON_PATH" \
  --max-time 900 \
  -X POST "https://api.perplexity.ai/v1/agent" \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$REQ_BODY")

if [[ "$HTTP_CODE" -ge 400 ]]; then
  echo "Error: Perplexity API returned HTTP $HTTP_CODE" >&2
  echo "--- response body ---" >&2
  cat "$JSON_PATH" >&2
  echo >&2
  exit 1
fi

# Guard against a successful HTTP response that still contains an error field
if jq -e '.error // empty' "$JSON_PATH" >/dev/null 2>&1; then
  echo "Error: Perplexity API returned an error payload" >&2
  jq '.error' "$JSON_PATH" >&2
  exit 1
fi

# Format response -> markdown
MODEL=$(jq -r '.model // "unknown"' "$JSON_PATH")
STATUS=$(jq -r '.status // "unknown"' "$JSON_PATH")
TOTAL_TOKENS=$(jq -r '.usage.total_tokens // 0' "$JSON_PATH")
TOTAL_COST=$(jq -r '.usage.cost.total_cost // 0' "$JSON_PATH")
CURRENCY=$(jq -r '.usage.cost.currency // "USD"' "$JSON_PATH")

{
  echo "# Research Report"
  echo
  echo "**Query:** $QUERY"
  echo "**Preset:** \`$PRESET\`"
  echo "**Model:** \`$MODEL\`"
  echo "**Status:** $STATUS"
  echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "**Tokens:** $TOTAL_TOKENS"
  echo "**Cost:** $TOTAL_COST $CURRENCY"
  echo
  echo "---"
  echo
  echo "## Answer"
  echo
  jq -r '
    [.output[]
      | select(.type == "message")
      | .content[]?
      | select(.type == "output_text")
      | .text
    ] | join("\n\n")
  ' "$JSON_PATH"
  echo
  echo
  echo "## Sources"
  echo
  SOURCES=$(jq -r '
    [.output[]
      | select(.type == "search_results")
      | .results[]?
    ]
    + [.output[]
      | select(.type == "fetch_url_results")
      | .contents[]?
      | {url, title, snippet: (.snippet // "")}
    ]
    | unique_by(.url)
    | to_entries
    | map(
        "\(.key + 1). [\(.value.title // .value.url)](\(.value.url))"
        + (if (.value.snippet // "") != ""
           then " — " + ((.value.snippet // "") | gsub("\\s+"; " ") | .[0:220])
           else "" end)
      )
    | .[]
  ' "$JSON_PATH")
  if [[ -z "$SOURCES" ]]; then
    echo "_No external sources returned (the agent answered from model knowledge)._"
  else
    echo "$SOURCES"
  fi
  echo
  echo "## Search Queries Issued"
  echo
  QUERIES=$(jq -r '
    [.output[]
      | select(.type == "search_results")
      | .queries[]?
    ] | unique | map("- " + .) | .[]
  ' "$JSON_PATH")
  if [[ -z "$QUERIES" ]]; then
    echo "_None recorded._"
  else
    echo "$QUERIES"
  fi
  echo
  echo "---"
  echo
  echo "Raw response: \`$JSON_PATH\`"
} > "$MD_PATH"

echo "$MD_PATH"
