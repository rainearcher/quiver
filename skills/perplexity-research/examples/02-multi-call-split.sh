#!/usr/bin/env bash
# Dependency-driven multi-call split.
# Call 1: survey the landscape.
# Call 2: deep-dive the 3 vendors that came out of call 1 (depends on call 1).
# Call 3: integration gotchas for the winner (depends on calls 1-2).
#
# Each call includes PRIOR FINDINGS from previous calls so the agent doesn't
# re-research ground that's already covered.

set -euo pipefail

OUT=./research
TOPIC=secrets-management
mkdir -p "$OUT/$TOPIC"

# -----------------------------------------------------------------------------
# CALL 1 — landscape survey
# -----------------------------------------------------------------------------
CALL1=$(bash ../scripts/research.sh \
  --preset advanced-deep-research \
  --output "$OUT" \
  --topic "$TOPIC" \
  --recency month \
  --instructions "$(cat <<'EOF'
GOAL
Survey the secrets-management tool landscape for a 1-3 engineer team
running a Node.js monorepo on Vercel + Render. Output feeds a shortlist
for deeper evaluation.

DELIVERABLE (this call only)
- One 10-row matrix of the top 10 tools, columns: pricing tier for 1-3
  seats, CLI-friendliness, ephemeral-container support, Vercel integration,
  Render integration.
- Top-3 shortlist recommendation with 2-sentence justification each.

DO NOT deep-dive any specific tool in this call — that's call 2.

EOF
)" \
  "Survey secrets-management tools suitable for a 1-3 engineer Node.js monorepo on Vercel + Render.")

echo "Call 1 output: $CALL1"

# In a real session, at this point the assistant would Read $CALL1,
# extract the shortlist, and pass it as PRIOR FINDINGS to call 2.
# For this example we hard-code a plausible shortlist.

PRIOR_1="PRIOR FINDINGS FROM CALL 1 (do not re-research):
Top-3 shortlist: Doppler, Infisical, 1Password Secrets Automation.
Key dimensions that differentiated them: CLI DX, Vercel + Render native
integration, ephemeral-container support. Bitwarden Secrets Manager was
ruled out for missing Render integration. HashiCorp Vault was ruled out
as overkill for this team size."

# -----------------------------------------------------------------------------
# CALL 2 — deep-dive the shortlist (depends on call 1)
# -----------------------------------------------------------------------------
CALL2=$(bash ../scripts/research.sh \
  --preset advanced-deep-research \
  --output "$OUT" \
  --topic "$TOPIC" \
  --recency month \
  --instructions "$(cat <<EOF
${PRIOR_1}

GOAL
Deep-dive the shortlist from call 1. Pick a winner for this team.

DELIVERABLE (this call only)
- Per-vendor section (max 800 words each): pricing for 1-3 seats, CLI
  commands that matter day-to-day, how secrets flow into Vercel and Render,
  audit-log capabilities, known outages or breach history.
- Final recommendation with a "pick X if ..., pick Y if ..." decision tree.

EOF
)" \
  "Deep-dive Doppler vs Infisical vs 1Password Secrets Automation for a 1-3 engineer Node.js monorepo on Vercel + Render.")

echo "Call 2 output: $CALL2"

# -----------------------------------------------------------------------------
# CALL 3 — integration gotchas for the winner (depends on calls 1-2)
# -----------------------------------------------------------------------------
# In a real session the winner is extracted from call 2. Here we assume Doppler.

PRIOR_2="PRIOR FINDINGS FROM CALLS 1-2 (do not re-research):
Winner: Doppler. Chosen for best Render + Vercel integration and lowest
friction CLI. Open question: how does Doppler behave in ephemeral-container
workflows (Daytona, GitHub Codespaces, Claude Code sandboxes) where agents
need short-lived scoped access?"

CALL3=$(bash ../scripts/research.sh \
  --preset advanced-deep-research \
  --output "$OUT" \
  --topic "$TOPIC" \
  --recency month \
  --instructions "$(cat <<EOF
${PRIOR_2}

GOAL
Write the ephemeral-container integration playbook for Doppler. This is
the final call in the series.

DELIVERABLE
- Step-by-step bootstrap for a fresh ephemeral sandbox: install Doppler
  CLI, authenticate with a service token, fetch scoped secrets, inject
  into child processes.
- 5-row table of failure modes (token leaked to logs, token committed to
  git, etc.) with detection + remediation for each.
- One "definitely don't do this" anti-pattern section.

EOF
)" \
  "Doppler integration playbook for ephemeral sandboxes (Daytona, Codespaces, Claude Code sandboxes).")

echo "Call 3 output: $CALL3"
echo
echo "Three-call sequence complete."
echo "  Call 1 (survey):       $CALL1"
echo "  Call 2 (deep-dive):    $CALL2"
echo "  Call 3 (integration):  $CALL3"
