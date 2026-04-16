# Troubleshooting

Common issues running `perplexity-research` and how to fix them.

## `PERPLEXITY_API_KEY not set`

Add the key to your shell env or `~/.claude/.env`:

```bash
export PERPLEXITY_API_KEY=pplx-...
```

If using `~/.claude/.env`, make sure your Claude Code session has sourced it — restart the CLI after first adding the key.

Create a key at https://www.perplexity.ai/account/api.

## HTTP 401 Unauthorized

The key is invalid, revoked, or expired. Generate a new one in the Perplexity dashboard.

## HTTP 429 Rate Limited

You hit Perplexity's per-key rate limit. The Agent API enforces concurrent-request and per-minute limits separate from their chat tier.

- Wait ~60 seconds and retry the same call.
- If it happens repeatedly, space out multi-call sequences by 30s+ between calls (sleep between them).
- Heavy users should check their plan tier in the Perplexity account dashboard.

## Timeout (no response after 15 minutes)

The script enforces a 15-minute `curl --max-time`. If you hit it:

- Reduce `--max-steps` (default is 10; try 6).
- Downgrade preset: `--preset pro-search` instead of `advanced-deep-research`.
- Narrow the query — overly broad queries cause the agent to loop through many steps.

## Empty "Sources" section

The agent answered from model knowledge without issuing search queries. This happens when:

- The query is too general (no named entities, time window, or specific claim to verify).
- The agent decided the answer was already well-established.

Fix:

- Add specificity: named entities, dates, jurisdictions, product versions.
- Set `--recency week` or `--recency month` to force fresh sources.
- Narrow `--domains` to force actual web fetches.

## Report ignored the format rules (no TL;DR / no Sources table / no Confidence & gaps)

The `--instructions` string was probably too long and the format block got truncated from the model's input. Fix:

- Shorten the context portion of `--instructions` (keep the format block intact).
- Move long context digests into the query itself or a follow-up call with `PRIOR FINDINGS` framing.

## Report truncated (sections missing, tables cut mid-row, lists cut mid-item)

The plan exceeded the per-call output ceiling (~16k tokens / ~10k words). Do NOT retry with the same scope — it will truncate again.

Follow the recovery workflow in SKILL.md Step 4:

1. Diff the report's TOC against its body. List what's missing or cut.
2. Quantify: "X sections, Y items, Z rows still needed."
3. Plan a follow-up call with a scope that fits the per-call budget (Step 2.5 in SKILL.md).
4. In the follow-up's `--instructions`, paste a ~200–400-word digest of completed sections under `PRIOR FINDINGS (do not re-research)`.
5. Run it and verify.

## Cost higher than expected

`advanced-deep-research` runs typically land in $0.30–$1.50. If you're seeing $2+:

- The `--instructions` block was very long (high input tokens).
- The agent ran all 10 `--max-steps` and fetched many URLs.
- Multiple large tables in the output increased output tokens.

The cost is always printed in the generated markdown. Surface it to the user and consider dropping to `deep-research` or `pro-search` for similar questions in the future.

## Agent didn't prioritize my preferred experts/domains

- Pass `--domains` to force a domain allowlist.
- Explicitly name experts in the query (e.g., "Reconcile the frameworks from <Expert A>, <Expert B>, <Expert C>").
- In `--instructions`, add a "Required sources" section listing names and expected publications.

If experts still don't appear in the output, check the "Confidence & gaps" section — the agent should explicitly flag when it couldn't find a named expert's work.

## `curl` or `jq` not installed

macOS: `brew install curl jq`
Debian/Ubuntu: `sudo apt install curl jq`
Alpine: `apk add curl jq`

Both are required — the script exits early if either is missing.
