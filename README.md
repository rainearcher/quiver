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

### `loom` — read and manage Loom videos from the shell

Transcripts, captions, AI summaries and action items out of Loom recordings, via the [`loom` CLI](https://github.com/rainearcher/mcp-loom) that ships inside the skill. Triggers on a pasted `loom.com` URL or anything Loom-shaped. Good for:

- "Summarize this loom" / "what did they say in this loom?"
- Pulling a full transcript, WebVTT captions, chapter markers or key takeaways
- Extracting action items across a batch of recordings ("to-dos from my last 10 looms")
- Listing or searching your library, reading comments and threaded replies
- Turning a recording into meeting notes, or grabbing the MP4 download URL
- Library management: rename, move, archive, pin, share to a space, Watch Later

**How it runs**: no MCP server, nothing to install, and nothing fetched from PyPI. The CLI is vendored into the skill at `skills/loom/vendor/`, so installing the skill installs the tool — `uvx` builds that local copy on first use (~0.3s) and caches it. `scripts/loom.sh` locates the vendored copy relative to its own path, so it works from any directory. Set `LOOM_BIN=loom` to use a `loom` already on your `PATH` instead. Human-readable text by default, `--json` for parsing, `-o PATH` so long transcripts land on disk instead of in the conversation, and `--dry-run` on every write.

**Prerequisites**:

- [`uv`](https://docs.astral.sh/uv/) on `PATH` (provides `uvx`), or `loom` installed already
- A Loom session cookie. Loom has no official API key, so the CLI talks to Loom as you.

**Setup**:

```bash
# Sign in at loom.com, then DevTools (F12) -> Application -> Cookies ->
# https://www.loom.com -> copy the VALUE of connect.sid (it starts with s%3A)
export LOOM_COOKIE='s%3A...'

# Verify everything is wired up, including one live read-only call
bash skills/loom/scripts/check-setup.sh
```

To make the cookie permanent, add the `export` to your shell rc (`~/.zshrc`, `~/.bashrc`) or `~/.claude/.env`, then restart the CLI. Cookies last about 30 days; when one expires every command exits `3` and says so.

**Updating the vendored CLI**: the copy under `skills/loom/vendor/` is stamped with the upstream commit it came from, and `scripts/sync-vendor.sh --check` fails if anyone edits it by hand. Do not patch `vendor/` directly — change [mcp-loom](https://github.com/rainearcher/mcp-loom), then re-vendor:

```bash
bash skills/loom/scripts/sync-vendor.sh /path/to/mcp-loom
bash skills/loom/scripts/sync-vendor.sh --check
```

**Usage**: paste a Loom link and ask for what you want — "summarize this", "what were the action items", "pull the transcript". The skill extracts the video ID from the URL, picks the cheapest command that answers the question, and writes long payloads to disk rather than dumping them into the conversation. Writes are confirmed with you first and dry-run before they touch your account.

See [`skills/loom/SKILL.md`](./skills/loom/SKILL.md) for the full 60-command reference, worked workflows, exit codes, and troubleshooting.

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

**Raine Soriano** — AI software engineer building EDA, agentic, and full-stack apps.

- GitHub: [@rainearcher](https://github.com/rainearcher)
- LinkedIn: [rainesoriano](https://www.linkedin.com/in/rainesoriano/)
- Email: [raine.a.soriano@gmail.com](mailto:raine.a.soriano@gmail.com)
