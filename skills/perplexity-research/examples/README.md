# Examples

Three patterns showing how to use this skill in practice. Each example includes the exact `--instructions` payload and a description of what to expect.

## 1. Simple focused query — [`01-simple-query.sh`](./01-simple-query.sh)

Single call, one clear deliverable, tight scope. Costs ~$0.30, takes ~2 min.

**When to use:** one decision to make, one audience, no prior context to preload.

## 2. Dependency-driven multi-call — [`02-multi-call-split.sh`](./02-multi-call-split.sh)

Three sequential calls where call 2 depends on what call 1 surfaces (the shortlist of vendors to deep-dive), and call 3 depends on calls 1–2 (the integration gotchas for the winning vendor).

**When to use:** the shape of later calls is genuinely unknown until earlier calls return. Don't force this structure if you already know the answer — prefer a single larger call with a tighter plan.

## 3. Expert-framework comparison — [`03-expert-comparison.sh`](./03-expert-comparison.sh)

Names 4 experts in the query so the agent searches for and directly compares their published frameworks. This pattern reliably produces higher-fidelity output than generic "what's the best approach" queries.

**When to use:** the question has established thought leaders whose frameworks you want to reconcile or choose between.

## Sample output — [`sample-report.md`](./sample-report.md)

An anonymized example of what `advanced-deep-research` produces: TL;DR → sections with citations → Sources table → Where sources disagree → Confidence & gaps.
