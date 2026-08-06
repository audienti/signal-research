# Signal Research

Signal Research is a Codex and Claude Code plugin for turning outbound ideas
and binary market-signal questions into source-backed target lists.

It now supports two complementary lanes:

- `signal-prospect-research`
  Start with an offer and premise, then work toward companies and likely buyers.
- `serper-binary-signal-research`
  Start with a yes-or-no public signal question, then use Serper-backed web
  search to find matching companies, domains, and LinkedIn company URLs.

## Best for

- building an account list for a new outbound motion
- pressure-testing whether a premise is strong enough to prospect against
- finding companies with public evidence that a problem is active
- identifying the smallest credible buyer set before writing outreach

## What the plugin does

The plugin adds two research skills:

- `signal-prospect-research`
  - turns an offer and premise into explicit research signals
  - looks for externally verifiable company evidence
  - ranks companies by evidence strength
  - identifies likely owners, operators, sponsors, or evaluators
  - returns a source-backed prospect brief with confidence and gaps

- `serper-binary-signal-research`
  - turns a binary signal question into query families
  - runs Serper-backed web search for named entities
  - separates publisher noise from real company matches
  - resolves official domains and LinkedIn company URLs
  - returns a goodput summary plus follow-up resolution jobs

## Codex requirements

This plugin ships a skill. It does not bundle its own MCP server or app connector.

It works inside Codex by using the tools already available in the current run.

### Required

- Codex plugin support with skill loading enabled
- access to native web research in the current run
- `python3` for the bundled helper scripts

### Recommended

- `Unipile`
  for LinkedIn account discovery, LinkedIn search, and Sales Navigator people search
- `Icypeas`
  for LinkedIn company URL discovery, profile URL discovery, and bulk scraping
- `Browser` or `Chrome`
  when the task requires direct page inspection in LinkedIn or Sales Navigator
- `SERPER_API_KEY`
  for live Serper-backed binary-signal runs, either in the environment or in
  `~/.codex/config.toml`

### What happens without them

- without `Unipile`, the plugin can still do company-level research from public
  web sources
- without `Icypeas`, LinkedIn identity resolution and profile verification are
  slower and weaker
- without `Browser` or `Chrome`, the plugin should not claim direct page-level
  Sales Navigator inspection
- without `SERPER_API_KEY`, the binary-signal lane can still produce the signal
  contract and query set, but it must not pretend the live search ran

## How it thinks

The two skills use adjacent but different sequences:

1. `signal-prospect-research`
   - `offer`
   - `premise`
   - `signals`
   - `company matches`
   - `people`

2. `serper-binary-signal-research`
   - `offer`
   - `signal question`
   - `match rule`
   - `query families`
   - `candidate entities`
   - `identity enrichment`
   - `ranked targets`

Both keep the research tied to observable evidence instead of generic category
matching.

## Typical inputs

The plugin works best when the request includes:

- the offer or product being sold
- either:
  - a one-sentence premise beginning with `This offer matters when...`
  - or a binary signal question such as `Has the company recently merged, been acquired, or acquired assets in the last 90 days?`
- the titles or buyer functions that matter most, when people resolution is
  needed
- how many companies and people are needed
- any geography, industry, size, or stage constraints

## What you get back

By default, the plugin returns a markdown research brief with:

- a short thesis or signal contract
- the signals or query families used
- ranked companies
- per-company evidence and source URLs
- selected people when the skill is working in buyer-resolution mode
- confidence and gaps
- the next best follow-up search or resolution job

If requested, it can also return JSON with these top-level keys:

- `offer`
- `premise`
- `signals`
- `companies`
- `summary`
- `gaps`

## Example prompts

- Turn this offer into premise, signals, target companies, and likely buyers.
- Find companies showing evidence that this problem is live.
- Given this signal question, find companies with public evidence that it is true.
- Use Serper-backed search to find companies that recently merged or acquired assets and resolve their domains and LinkedIn company URLs.
- Rank the best-fit accounts for this motion and identify the smallest credible buyer set.
- Research likely buyers at these companies and explain why each one matters.

## Repository contents

- `.codex-plugin/plugin.json`: Codex plugin manifest
- `.claude-plugin/plugin.json`: Claude Code manifest
- `skills/signal-prospect-research/SKILL.md`: premise-to-prospect research skill
- `skills/serper-binary-signal-research/SKILL.md`: Serper-backed binary-signal skill
- `skills/serper-binary-signal-research/scripts/resolve_memory.py`: memory resolver and scaffolder
- `skills/serper-binary-signal-research/scripts/run_serper_search.py`: Serper job runner
- `skills/serper-binary-signal-research/scripts/normalize_signal_search_results.py`: result normalizer and goodput ledger builder
- `skills/serper-binary-signal-research/memory/`: skill-local memory notes and templates
- `skills/serper-binary-signal-research/examples/`: synthetic smoke-test fixtures

## Validation

```bash
python3 /Users/williamflanagan/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 /Users/williamflanagan/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/signal-prospect-research
python3 /Users/williamflanagan/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/serper-binary-signal-research
python3 skills/serper-binary-signal-research/scripts/resolve_memory.py --offer https://example.com/path --signal "Has the company acquired assets in the last 90 days?"
python3 skills/serper-binary-signal-research/scripts/run_serper_search.py --query "\"Example Co\" official site" --dry-run
python3 skills/serper-binary-signal-research/scripts/normalize_signal_search_results.py --input skills/serper-binary-signal-research/examples/ma_rationalization_runs.json --archetype ma_rationalization
```

## Install source

Marketplace entries can reference this repository:

```text
https://github.com/omalab/signal-prospect-research.git
```
