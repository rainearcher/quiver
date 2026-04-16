---
name: perplexity-research
description: Run deep research / advanced research / "perplexity research" on a topic — multi-step web browsing with citations via Perplexity's Agent API. Use when the user asks for a sourced brief, competitive analysis, competitor research, market research, GTM or landing-page audit, feature comparison, market stack-rank for expansion, investor-memo background, due-diligence brief, "investigate X thoroughly", "research report on Y", "build out [initiative]", or any request that needs multi-step browsing + inline citations. Enforces the GTM deep-research methodology from Growth Unhinged (growthunhinged.com/p/deep-research-for-gtm) — gathers goal + product context + constraints + source preferences, drafts a research plan for approval before spending API credit, budgets against the per-call output ceiling to prevent truncation, and requires a structured report (TL;DR, comparison tables, inline citations, Sources table with primary-source priority, Where-sources-disagree, Confidence & gaps). Default preset — advanced-deep-research (Claude Opus 4.6 + web_search + fetch_url). Requires PERPLEXITY_API_KEY.
metadata:
  author: Raine Soriano (@rainearcher)
  version: "1.0.0"
---

# Perplexity Deep Research

Call the Perplexity Agent API (`POST /v1/agent`) to perform multi-step browsing research with citations. **Before** calling the API, this skill requires a structured intake + plan-approval loop so the agent uses the right sources, has the right context, and returns a report in a skimmable format.

## Methodology

This skill is a programmatic enforcement of the Growth Unhinged deep-research playbook for GTM: https://www.growthunhinged.com/p/deep-research-for-gtm. The article's five recommendations map 1:1 to the steps below:

| Article recommendation | Enforced by |
|---|---|
| Provide comprehensive context (goal, GTM/product, constraints, preferred sources) | Step 1 — five-dimension intake |
| Request a research plan first, approve before running | Step 2 — plan-approval gate (no API spend without approval) |
| Point to high-quality sources; prefer primary over secondary; cite everything | Format block — Sources table, primary-source priority, inline citations required |
| Specify report format; summaries and tables over prose (Pyramid Principle) | Format block — TL;DR first, comparison tables, conclusions before background |
| Structure the prompt (`<goal>`, `<context>`, `<sources>`, `<instructions>`) | `--instructions` block layout |

The per-call output-budget check (Step 2.5) and multi-call sequencing (Step 2.6) are additions on top of the article, to prevent the silent-truncation failure mode that large GTM plans (hook libraries, 30-day calendars, vendor matrices) routinely hit.

## Prerequisites

- `PERPLEXITY_API_KEY` available in the environment (get one at https://www.perplexity.ai/account/api)
- `curl` and `jq` installed

## When to Use

- User explicitly asks for "deep research", "advanced research", or "perplexity research"
- User needs a sourced brief (company, person, event, technology, regulation)
- Questions that require multi-step browsing and synthesis across many sources
- Questions requiring very recent information with inline citations

**Do NOT use for:**
- Simple factual lookups ("what's the current price of X") — use `WebSearch` / `WebFetch` instead (cheaper, faster)
- Simple binary comparisons ("is tool A or B better") — a single `WebSearch` round usually resolves this
- Authenticated or paywalled content (Perplexity can't log in)
- Quick code edits or questions answerable from the codebase — inline is faster
- Verifying a specific fact you already have context on — `WebFetch` is precise enough

## Workflow (MANDATORY — do not skip steps)

Deep research runs cost real money and take 2–5 minutes. A bad run wastes both. Always follow this loop:

### Step 1 — Audit the initial query, then ask ONLY for what's missing

First, read the user's initial query and determine which of the five context dimensions below are already answered, which are partially answered, and which are missing entirely. Do **not** re-ask things the user has already told you.

The five dimensions:

1. **Goal & motivation** — what they're trying to achieve, how the output will be used (decision, doc, pitch, strategy), prior work already done.
2. **Product / situation context** — the company/product/role, how it operates, relevant setup details (size, stage, GTM, audience).
3. **Constraints** — budget, deadlines, headcount, legal/compliance, ruled-out options, non-negotiables.
4. **Preferred sources** — named experts/creators, publication types (academic, primary/gov data, forums, analysts, SEC filings, GitHub, etc.), allowed vs. blocked domains, recency window.
5. **Scope boundaries** — what's explicitly out of scope, assumptions the agent should NOT make.

Decide whether to ask:

- **If all five dimensions are sufficiently answered** → skip clarification entirely and go straight to Step 2 (draft the plan). Do not ask questions just to confirm what you already know.
- **If one or more dimensions are missing or ambiguous** → use `AskUserQuestion` to ask **only about the gaps**, in a single consolidated block. Explicitly list what you already understood (so the user can correct you) and what you still need.
- **If the user says "just go" / "use your judgment"** → skip to Step 2 and list your assumptions for each missing dimension in the plan so the user can still correct them there.

Bias toward fewer questions. A well-specified one-paragraph query often needs zero clarification — go straight to the plan.

### Step 2 — Draft a research plan and get approval

Before calling the API, draft a **research plan** in your response and ask the user to approve or edit it. The plan must include:

- **Research questions** — the specific sub-questions the agent will answer
- **Methodology** — how it will evaluate/compare options, what framework it will use
- **Source strategy** — which source types it will prioritize, which it will avoid, any domain filters or recency window
- **Report structure** — section headings the final report will use
- **Deliverables** — beyond prose, will there be tables, comparison matrices, templates, checklists, code snippets?
- **Open assumptions** — anything you're guessing about that the user should correct

**Wait for explicit approval** ("looks good", "go", "run it", edits to the plan, etc.) before proceeding. If the user edits the plan, re-confirm before running.

### Step 2.5 — Output budget check (MANDATORY — prevents truncation)

The `advanced-deep-research` preset has a practical output ceiling around **~16k tokens / ~10k words** per response. Plans that exceed this get silently truncated — sections listed in the TOC simply won't appear, and large deliverables (hook libraries, N-day calendars, anti-pattern catalogs) get cut off mid-table. You must budget against this ceiling BEFORE running.

**Per-call output budget (hard limits):**

| Item | Max per call |
|---|---|
| Major sections (H2) | 8 |
| Large tables (6+ rows, 4+ columns) | 4 |
| Itemized libraries/catalogs (hooks, templates, examples, ideas) | 10 items total across all libraries |
| Long-form deliverables (N-day calendars, shot-by-shot scripts, full playbooks) | 1 |
| Total prose (excluding tables) | ~4,000 words |

**Red flags that mean your plan is too big for one call:**
- TOC has >8 sections
- Plan promises "25+ hooks" / "30-day calendar" / "20 templates" alongside multiple matrices
- Plan asks for multiple large deliverables in the same call (e.g. hook library AND content calendar AND shot-by-shot template AND anti-pattern catalog)
- Plan covers >1 distinct audience segment or >1 distinct goal in depth

**If the plan fits the budget** → proceed to Step 3.

**If the plan exceeds the budget** → split it into a sequential multi-call plan (see "Multi-call sequencing" below) and present that to the user for approval instead.

### Step 2.6 — Multi-call sequencing (for large scopes OR dependent research)

There are **two separate reasons** to split into multiple sequential calls, and both use the same mechanics:

**(A) Budget-driven split** — the plan exceeds the per-call output ceiling from Step 2.5. Split into focused calls, each with ONE primary deliverable.

**(B) Dependency-driven split** — call N's scope depends on call N-1's findings. Example: a landscape survey of vendors (call 1) informs which 3 vendors get deep-dives (calls 2–4). This isn't about size — it's about letting later calls react to what earlier calls surface. Don't try to pre-plan everything upfront when you genuinely don't know the answer until you've run call 1.

**Rules for any multi-call split:**

1. Run calls **sequentially**, not in parallel — each call should be able to cite or build on prior outputs.
2. Each call must have ONE primary deliverable focus.
3. Each call must stay within the per-call budget from Step 2.5.
4. Each call must be individually valuable — don't create calls that only make sense in combination.
5. In each subsequent call's `--instructions`, paste the **key findings** from prior calls (not the full report — just the load-bearing conclusions, ~200–400 words) under a `PRIOR FINDINGS (do not re-research)` header so the agent doesn't waste steps re-covering ground.
6. After each call completes, `Read` the output, verify nothing was truncated (check that every section in the call's TOC is present and no tables end mid-row), and briefly summarize it to the user before kicking off the next call.

Present the split as:
```
This plan needs N sequential calls because <budget / dependency reason>:
  Call 1 — <focus>  (~$X, ~3 min)
  Call 2 — <focus>  (~$X, ~3 min)
  ...
Total estimated cost: $X. Approve split, or tell me what to cut.
```

Wait for explicit approval of the split before running any call. If the user edits the split, re-confirm.

### Step 3 — Run the research

Once approved, invoke the script. Pass the approved plan + context + format requirements via `--instructions`. Use `--domains` and `--recency` flags when the user specified them.

**Always pass `--topic <slug>`** so the output lands in a topic subdirectory under `./docs/research/`. Before invoking, inspect the existing subdirectories (`ls docs/research/`) and either reuse an existing slug that matches the research area or create a new short kebab-case slug. If you're creating a new topic, pick something durable — a slug you'd still use for the next 3–5 reports in the same area, not a one-off phrase from the current question. Good slug shapes: `vendor-comparison`, `competitor-analysis`, `regulation-update`, `<product-area>`. Bad slug shapes: `doppler-vs-vault-2026` (too specific and date-coupled).

```bash
bash ./skills/perplexity-research/scripts/research.sh \
  --preset advanced-deep-research \
  --output ./docs/research \
  --topic <topic-slug> \
  --instructions "$(cat <<'EOF'
<paste the approved plan + context + format requirements here>
EOF
)" \
  "<the research question, refined from the approved plan>"
```

### Step 4 — Read the report and summarize

The script prints the markdown path. Always `Read` that file before reporting back.

**Truncation check (mandatory):**
1. Confirm every section listed in the report's own TOC is actually present in the body.
2. Confirm no table ends mid-row and no itemized list ends mid-item.
3. Confirm the "Sources", "Where sources disagree", and "Confidence & gaps" sections at the end are present.

**Truncation recovery workflow.** If any of those are missing → the output was truncated. Do this:

1. **Identify exactly what's missing.** Diff the report's TOC against its body. List the missing sections, incomplete tables (note the last complete row), and cut-off list items (note the last complete item).
2. **Quantify the remaining work.** "X sections, Y items, Z rows still needed."
3. **Propose a focused follow-up call** with a scope that fits the per-call budget. Do NOT retry the same scope — it will truncate again.
4. **Include `PRIOR FINDINGS` in the follow-up's `--instructions`** — paste a ~200–400-word digest of the completed sections so the agent doesn't re-research them. Explicitly say "do not re-cover X, Y, Z; focus only on A, B, C."
5. **Tell the user** what was truncated and show the follow-up plan before running.

Surface: key insights, the USD cost from the report, any notable source disagreements, and a truncation flag if applicable.

## Power patterns

These patterns reliably improve output quality. Use them in Step 2 when drafting the plan.

### Cite specific experts or frameworks in your query

Naming 3–6 relevant experts, authors, creators, or named frameworks in the query gives the agent concrete sources to search for and compare. The report becomes a comparison of known viewpoints rather than an anonymous synthesis.

Example query fragments:
- "Compare the frameworks used by <Expert A>, <Expert B>, and <Expert C> for..."
- "Per the <Named Framework> methodology, evaluate..."
- "Reconcile the approaches recommended by <Author A> (in <book/blog>) vs <Author B>..."

Works best when the experts publish regularly (papers, videos, posts, talks) — the agent can fetch their primary material.

### Specify quantified deliverables

Instead of asking for "a good number of examples", state the exact count and shape. This locks scope, prevents drift, and surfaces when you're over budget (cross-reference Step 2.5).

Good deliverable specs:
- "A comparison matrix: 8 rows (one per vendor), 5 columns (price, latency, auth, SDKs, compliance)"
- "A library of exactly 10 templates, grouped into 3 categories"
- "A 14-day sequence with one item per day"

Avoid: "a comprehensive library", "several examples", "many options" — these are invitations to truncate or waver.

### Pre-load context in `--instructions`, not the query

The query should stay a tight 1–2 sentences. Anything about the user's situation, constraints, prior decisions, or source preferences goes in `--instructions`. This keeps the agent's search queries focused while the synthesis stays grounded in your context.

## Required format instructions (always include in `--instructions`)

Every run must embed these format requirements in the `--instructions` string so the report is skimmable and trustworthy:

```
SCOPE & SIZE CONSTRAINT (read first — this controls what you include):

This single response has a hard output ceiling. Do NOT try to cover
everything — if forced to choose, PRIORITIZE COMPLETENESS of the sections
you do include over breadth of sections. A shorter, fully-delivered report
is strictly better than a longer report that gets cut off mid-section,
mid-table, or mid-list.

Concrete limits for THIS response:
- Maximum 8 H2 sections (including the mandatory Sources, Where-sources-
  disagree, and Confidence-and-gaps sections — budget accordingly).
- Maximum 4 large tables (6+ rows AND 4+ columns).
- Maximum 10 items TOTAL across any itemized libraries/catalogs in this
  response (hook lists, templates, examples). If the plan asks for more
  than 10, deliver the 10 highest-value items and state clearly: "N of M
  delivered in this call — remaining items should be requested in a
  follow-up call."
- Maximum 1 long-form deliverable (N-day calendar, full shot-by-shot
  script, complete playbook).
- Target ~4,000 words of prose excluding tables.

Before writing any section, verify the full list of sections + deliverables
will fit. If not, CUT sections from the end of the plan rather than
shortening every section. Always fully deliver Sources, Where sources
disagree, and Confidence & gaps — these are mandatory and must not be
sacrificed.

REPORT FORMAT REQUIREMENTS — follow exactly:

1. Start with a TL;DR section (3–6 bullets) containing the key insights and
   recommendations before any detail.
2. Every major section must start with its own 1–2 sentence summary, then
   details. Lead with conclusions, not background.
3. Use tables or comparison matrices instead of prose blocks wherever options,
   tools, vendors, or data points are being compared.
4. Use inline citations [1], [2], ... for every factual claim. No uncited
   claims.
5. Include a "Sources" table at the end with columns:
   | # | Source | Type (primary data / academic / news / forum / blog / vendor) | Year | Used for |
6. Include a "Where sources disagree" section. For any data point where
   sources give different numbers or conclusions, show both, name the sources,
   and explain the likely reason (methodology, date, bias, sample size).
7. Prioritize primary sources (government data, SEC filings, peer-reviewed
   research, official docs, first-party benchmarks) over secondary sources
   (news articles, blog summaries). Flag when only secondary sources are
   available.
8. If the user specified preferred experts/creators/domains, prioritize those
   and explicitly note when their views were or were not found.
9. End with a "Confidence & gaps" section: what's well-supported, what's
   shaky, what couldn't be answered and why.
```

Append the user's goal, product context, constraints, source preferences, and the approved research plan above these format rules.

## Script options

```bash
--preset NAME       advanced-deep-research (default) | deep-research | pro-search | fast-search
--max-steps N       1–10 (default 10)
--output DIR        output directory (default ./docs/research)
--topic SLUG        subdirectory under --output for this topic (kebab-case);
                    created if missing. Pass this on every run.
--domains a,b,c     comma-separated domain allowlist
--recency PERIOD    day | week | month
--instructions STR  context + plan + format requirements (see above)
```

## Presets

| Preset | Model | Typical latency | Use for |
|---|---|---|---|
| `fast-search` | grok-4-1-fast | seconds | Quick lookups |
| `pro-search` | gpt-5.1 | ~30–60s | Balanced sourced answers |
| `deep-research` | gpt-5.2 | ~1–3 min | In-depth analysis |
| `advanced-deep-research` (default) | claude-opus-4-6 | ~2–5 min | Institutional-grade research |

## Typical costs (advanced-deep-research preset)

Observed across 24 production runs:

| Report shape | Prose | Tables | Typical cost |
|---|---|---|---|
| Focused brief (1 topic, 1–2 deliverables) | ~2,500 words | 1–2 | $0.10 – $0.40 |
| Standard report (full 8-section structure) | ~4,000 words | 3–4 | $0.50 – $1.00 |
| Maximum-size single call (all budget used) | ~5,500 words | 4+ | $1.00 – $2.00 |

Lighter presets cost significantly less — `fast-search` is often under $0.02. The cost is always printed in the generated markdown report; surface it back to the user.

## Output files

Written to `<--output>/<--topic>/` (or just `<--output>/` if `--topic` is omitted):

- `<query-slug>-<timestamp>.md` — formatted report (query, answer, sources, search queries, usage, cost)
- `<query-slug>-<timestamp>.json` — raw API response

Only the markdown path is echoed to stdout. Always `Read` the markdown before reporting. Surface the USD cost — runs can cost several cents to a few dollars.

## Troubleshooting

See `./TROUBLESHOOTING.md` (alongside this SKILL.md) for detailed recovery steps. Quick reference:

- **`PERPLEXITY_API_KEY not set`** — add to shell env or `~/.claude/.env`
- **HTTP 401** — key invalid or expired
- **HTTP 429** — rate limited; wait 60s and retry
- **Timeout** — reduce `--max-steps` or switch to `--preset pro-search`
- **Empty Sources section** — agent answered from model knowledge; re-run with a more specific query, `--recency week`, or tighter `--domains`
- **Report ignores format rules** — the format block may have been truncated; shorten the context portion of `--instructions` and re-run
- **Report truncated** — follow the recovery workflow in Step 4
