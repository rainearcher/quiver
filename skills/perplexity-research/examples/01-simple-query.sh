#!/usr/bin/env bash
# Simple focused query — one deliverable, one topic, single call.
# Expected: ~2 min, ~$0.30, ~3000-word report with 4-8 sources.

set -euo pipefail

bash ../scripts/research.sh \
  --preset advanced-deep-research \
  --output ./research \
  --topic vendor-comparison \
  --recency month \
  --instructions "$(cat <<'EOF'
GOAL
Help a small SaaS team (10 engineers, early Series A) pick between
Sentry, Datadog, and Rollbar for error tracking. Output will drive a
single procurement decision this quarter.

CONSTRAINTS
- Budget: under $500/month total
- Must support Node.js + React Native
- SOC 2 required (we sell to mid-market)

SCOPE
In scope: pricing, feature parity, developer experience, integration depth
Out of scope: log management (we have Papertrail), APM (not buying yet)

DELIVERABLES
- One comparison matrix: 3 rows (vendors) × 6 columns (price tier for our
  volume, Node SDK quality, RN SDK quality, SOC 2 status, free tier shape,
  onboarding friction)
- One "gotchas" section per vendor (300 words max each)
- One clear recommendation with justification

EOF
)" \
  "Compare Sentry vs Datadog vs Rollbar for a 10-engineer SaaS team on Node.js + React Native, under \$500/month, SOC 2 required."
