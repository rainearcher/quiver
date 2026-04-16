#!/usr/bin/env bash
# Expert-framework comparison.
# Naming specific experts in the query triggers the agent to search for
# and compare their published frameworks directly, producing higher-fidelity
# output than a generic "what's the best approach" query.

set -euo pipefail

bash ../scripts/research.sh \
  --preset advanced-deep-research \
  --output ./research \
  --topic hiring-frameworks \
  --instructions "$(cat <<'EOF'
GOAL
Build a hiring-for-senior-engineers framework for a small startup. Output
will anchor a written interview rubric used by 3 interviewers.

PREFERRED EXPERTS (search for their published work explicitly)
- Will Larson — "Staff Engineer" book, lethain.com blog
- Charity Majors — honeycomb.io blog, "The Engineer/Manager Pendulum"
- Lara Hogan — wherewithall.com, "Resilient Management"
- Camille Fournier — skamille.medium.com, "The Manager's Path"

DELIVERABLE
- One reconciliation matrix: 4 rows (experts) × 5 columns (core hiring
  criteria each expert emphasizes). Flag disagreements explicitly.
- One merged rubric that resolves the disagreements with a stated
  reasoning for each resolution.
- 5-item interview question bank drawn from the experts' own suggestions.

CONFIDENCE EXPECTATION
- If you can't find a primary-source framework from one of the experts,
  say so in Confidence & gaps — DO NOT fabricate or substitute.

EOF
)" \
  "Compare hiring-for-senior-engineers frameworks from Will Larson, Charity Majors, Lara Hogan, and Camille Fournier, and merge them into a single rubric."
