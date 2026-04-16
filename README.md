# quiver

A collection of Claude Code skills and plugins by [Raine Soriano](https://github.com/rainearcher). Each skill is an arrow you can pull out when you need it.

## Install

The skills work with Claude Code, OpenCode, Codex, Cursor, and 40+ other agents via the [skills CLI](https://github.com/vercel-labs/skills):

```bash
# Install a specific skill
npx skills add rainearcher/quiver perplexity-research

# Or browse all skills interactively
npx skills add rainearcher/quiver
```

Claude Code users can also install via the plugin marketplace:

```
/plugin marketplace add rainearcher/quiver
/plugin install perplexity-research@quiver
```

From the shell (non-interactive):

```bash
claude plugin marketplace add rainearcher/quiver
claude plugin install perplexity-research@quiver
```

## Skills

### `perplexity-research` — deep web research with citations

Multi-step web browsing via Perplexity's Agent API, enforced with a plan-approval workflow. Good for:

- Competitive analysis & competitor research
- Market research, GTM audits, landing-page audits
- Feature comparisons, vendor matrices
- Market stack-rank for expansion
- Investor-memo background, due-diligence briefs
- Any "sourced brief" or "research report" that benefits from many sources + inline citations

**Methodology**: enforces the [Growth Unhinged GTM deep-research playbook](https://www.growthunhinged.com/p/deep-research-for-gtm) — five-dimension intake, plan approval before API spend, per-call output-budget gating, and a structured sourced report (TL;DR, comparison tables, inline citations, Sources table, Where-sources-disagree, Confidence & gaps).

**Prerequisites**:

- A Perplexity API key — get one at https://www.perplexity.ai/account/api
- `curl` and `jq` (pre-installed on most Unix systems)

**Setup**:

```bash
# After installing the skill
export PERPLEXITY_API_KEY=pplx-...

# Verify everything is wired up
bash skills/perplexity-research/scripts/check-setup.sh
```

To make the key permanent, add the `export` to your shell rc (`~/.zshrc`, `~/.bashrc`) or `~/.claude/.env`, then restart the CLI.

**Usage**: ask your agent for "deep research on X" or "a sourced brief on Y". The skill will gather context, draft a research plan, wait for your approval, then run the research and write a markdown report to `./docs/research/<topic>/`.

A typical run takes 2–5 minutes and costs $0.30–$1.50. See [`skills/perplexity-research/SKILL.md`](./skills/perplexity-research/SKILL.md) for the full workflow and [`skills/perplexity-research/TROUBLESHOOTING.md`](./skills/perplexity-research/TROUBLESHOOTING.md) for recovery from HTTP 429, empty Sources, truncation, etc.

**Examples**: see [`skills/perplexity-research/examples/`](./skills/perplexity-research/examples/) for simple queries, dependency-driven multi-call splits, and expert-comparison patterns.

## Updating

```
/plugin marketplace update quiver
```

Claude Code refreshes the marketplace and pulls any plugin changes. For `npx skills`, run `npx skills update`.

## Uninstalling

Claude Code:

```
/plugin uninstall perplexity-research@quiver
```

Skills CLI:

```bash
npx skills remove perplexity-research
```

## Contributing

Issues and PRs welcome at https://github.com/rainearcher/quiver. Each skill lives under `skills/<name>/` with its own `SKILL.md`, scripts, examples, and troubleshooting doc.

## License

MIT — see [LICENSE](./LICENSE).

## Author

Raine Soriano ([@rainearcher](https://github.com/rainearcher))
