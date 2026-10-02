# Signal Prospect Research

Signal Prospect Research is a free plugin for Claude Code and Codex. Tell it
what you sell and why it matters, and it gives you back a ranked list of
companies that show public signs of that problem right now, the person at each
company most likely to care, and the sources behind each pick. Run it each week
and you have a fresh target list built from evidence, not guesses.

Instead of starting with a broad ICP guess, it helps an agent work from:

- what you sell
- why it matters
- what observable signals would prove that

to:

- which companies show those signals
- which people at those companies are most likely to care
- which sources support the recommendation

Watch the tutorial: video coming soon.

## Install

The plugin is listed in the Audienti marketplace
([audienti/plugins](https://github.com/audienti/plugins)) as
`signal-prospect-research`. Add the marketplace once, then install the plugin.

### Claude Code

In a Claude Code session:

```text
/plugin marketplace add audienti/plugins
/plugin install signal-prospect-research@audienti
```

Or from your terminal:

```bash
claude plugin marketplace add audienti/plugins
claude plugin install signal-prospect-research@audienti
```

If the install says to check your access rights, run it again with
`CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` set. That makes Claude Code download over
HTTPS instead of SSH.

### Codex

From your terminal:

```bash
codex plugin marketplace add audienti/plugins
codex plugin add signal-prospect-research@audienti
```

Or, after adding the marketplace, type `/plugins` inside Codex and install
**signal-prospect-research** from the `audienti` marketplace.

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

## You'll need

This plugin ships a skill. It does not bundle its own MCP server or app
connector. It uses the tools already available in your Claude Code or Codex
session.

### Required

- **Claude Code or Codex**, with plugins (skills) turned on.
- **Web search** turned on in the session. Company research comes from
  public web sources.
- Your own model usage. The plugin runs on your Claude or Codex account.

### Optional (makes the people part stronger)

- **Unipile**, connected as a tool, for LinkedIn account lookup, LinkedIn
  search, and Sales Navigator people search.
- **Icypeas**, connected as a tool, for finding LinkedIn company and profile
  URLs and checking them in bulk.
- **A browser tool** (Browser or Chrome), when you want it to look directly at
  LinkedIn or Sales Navigator pages.

These are third-party services with their own accounts and terms.

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
- `.claude-plugin/plugin.json`: Claude Code plugin manifest
- `skills/signal-prospect-research/SKILL.md`: main research skill
- `skills/signal-prospect-research/references/`: output template, signal shape, and tool recipes

## Install source

Marketplace entries can reference this repository:

```text
https://github.com/audienti/signal-research.git
```
