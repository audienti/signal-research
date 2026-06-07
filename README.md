# Signal Prospect Research

Signal Prospect Research helps you turn an outbound idea into a ranked list of target companies and likely buyers.

Instead of starting with a broad ICP guess, it helps an agent work from:

- what you sell
- why it matters
- what observable signals would prove that

to:

- which companies show those signals
- which people at those companies are most likely to care
- which sources support the recommendation

## Best for

- building an account list for a new outbound motion
- pressure-testing whether a premise is strong enough to prospect against
- finding companies with public evidence that a problem is active
- identifying the smallest credible buyer set before writing outreach

## What the plugin does

The plugin adds a research skill that:

- turns an offer and premise into explicit research signals
- looks for externally verifiable company evidence
- ranks companies by evidence strength
- identifies likely owners, operators, sponsors, or evaluators
- returns a source-backed prospect brief with confidence and gaps

## Codex requirements

This plugin ships a skill. It does not bundle its own MCP server or app connector.

It works inside Codex by using the tools already available in the current run.

### Required

- Codex plugin support with skill loading enabled
- access to native web research in the current run

### Recommended

- `Unipile`
  for LinkedIn account discovery, LinkedIn search, and Sales Navigator people search
- `Icypeas`
  for LinkedIn company URL discovery, profile URL discovery, and bulk scraping
- `Browser` or `Chrome`
  when the task requires direct page inspection in LinkedIn or Sales Navigator

### What happens without them

- without `Unipile`, the plugin can still do company-level research from public web sources
- without `Icypeas`, LinkedIn identity resolution and profile verification are slower and weaker
- without `Browser` or `Chrome`, the plugin should not claim direct page-level Sales Navigator inspection

## How it thinks

The skill uses a simple sequence:

1. `offer`
2. `premise`
3. `signals`
4. `company matches`
5. `people`

That keeps the research tied to observable evidence instead of generic category matching.

## Typical inputs

The plugin works best when the request includes:

- the offer or product being sold
- a one-sentence premise beginning with `This offer matters when...`
- the titles or buyer functions that matter most
- how many companies and people are needed
- any geography, industry, size, or stage constraints

## What you get back

By default, the plugin returns a markdown research brief with:

- a short thesis
- the signals used
- ranked companies
- per-company evidence and source URLs
- selected people and why they matter
- confidence and gaps
- the next best follow-up search

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
- Rank the best-fit accounts for this motion and identify the smallest credible buyer set.
- Research likely buyers at these companies and explain why each one matters.

## Repository contents

- `.codex-plugin/plugin.json`: Codex plugin manifest
- `skills/signal-prospect-research/SKILL.md`: main research skill
- `skills/signal-prospect-research/references/`: output template, signal shape, and tool recipes

## Install source

Marketplace entries can reference this repository:

```text
https://github.com/omalab/signal-prospect-research.git
```
