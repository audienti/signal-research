---
name: serper-binary-signal-research
description: Turn a yes-or-no market signal question into Serper-backed search queries, source-backed company matches, and enriched company identities. Use when the user asks to find companies or people that likely satisfy a binary public signal such as recent M&A, hiring, expansion, layoffs, leadership change, compliance activity, or vendor rationalization triggers.
---

# Serper Binary Signal Research

## Goal

- Turn a binary signal question into a tight research contract.
- Find companies or people with real public evidence that the signal is live.
- Return usable targets with domains and LinkedIn company URLs when they can be resolved.

## Default stance

- This skill is read-only by default.
- Optimize for `goodput`, not topical relevance.
- A result only counts as success when it becomes a source-backed target you would actually research or message further.

## Inputs to normalize if missing

- What is the offer or product being sold.
- What is the binary signal question.
- Why the signal matters to the offer.
- Whether the target entity is `company`, `person`, or `both`.
- The desired recency window.
- The titles or buyer functions that matter, if people resolution is needed.
- How many targets are needed.

If the user gives a loose explanation, normalize it into those fields before searching.

## Core model

Use this exact sequence:

1. `offer`
2. `signal question`
3. `match rule`
4. `query families`
5. `candidate entities`
6. `identity enrichment`
7. `ranked targets`

Use `references/signal-shape.md`.

## Workflow

### 1) Inspect memory

- Read `memory/lessons.md` first.
- Run:
  `python3 scripts/resolve_memory.py --offer "<offer_or_url>" --signal "<signal_question>" --scaffold`
- Use the output to find:
  - `memory/offers/`
  - `memory/signals/`
  - `memory/offer_signals/`
  - `memory/seed_packs/`
  - `memory/run_ledgers/`
- Treat these notes as priors, not truth.

### 2) Normalize the signal contract

For the signal, define:

- `name`
- `question`
- `scope`
- `why_it_matters`
- `match_rule`
- `observation_methods`
- `archetype`

Pick the closest archetype from `references/query-archetypes.md`.

If the user asks for a window like `last 90 days`, convert that into an exact absolute date in the query using `after:YYYY-MM-DD`. Do not rely on vague relative phrasing.

### 3) Build query jobs

- Build 3 to 8 query jobs across distinct query families.
- Prefer:
  - direct signal evidence
  - dated news coverage
  - company-site or press-release evidence
  - LinkedIn company URL resolution
- Reuse proven seed patterns from `memory/seed_packs/` before inventing fresh variants.
- Save the jobs to JSON and run:
  `python3 scripts/run_serper_search.py --jobs <jobs.json>`

### 4) Review the first-pass run

- Run:
  `python3 scripts/normalize_signal_search_results.py --input <runs.json> --archetype <archetype>`
- Inspect:
  - raw result counts
  - dated evidence counts
  - candidate company counts
  - enriched target counts
  - follow-up query jobs
- Stop if the run is only publisher noise, stale evidence, or decorative relevance.

### 5) Enrich identities

- For companies missing domains, run the normalizer's follow-up jobs for official-site resolution.
- For companies missing LinkedIn URLs, run the normalizer's follow-up jobs for `site:linkedin.com/company`.
- If the user asked for people and the company fit is strong, resolve people only after the company evidence is good enough to justify it.

### 6) Rank targets

For each company target, return:

- company name
- company domain
- LinkedIn company URL if found
- 1 to 3 signal evidence items
- observed dates when available
- confidence
- gaps or unresolved fields

If people are requested, add only the smallest credible set.

### 7) Update memory

- Update `memory/lessons.md` when a rule should persist across signals.
- Update `memory/offers/` when the learning is offer-specific.
- Update `memory/signals/` when the learning is signal-specific.
- Update `memory/offer_signals/` when the learning depends on the exact offer plus signal pairing.
- Update `memory/seed_packs/` when a query family, source pattern, or enrichment pattern proves durable.
- Update `memory/run_ledgers/` after every live run using the normalizer output.

## Research rules

- The signal question must be externally checkable.
- Recent evidence beats evergreen category fit.
- Publisher noise is not target evidence.
- Do not claim a company matches the signal if the evidence is only implied.
- Do not call something `last 90 days` unless the query or source dates actually support that.
- Separate `raw relevance` from `verified target`.
- Company resolution comes before people hunting.
- If the signal is weak on the public web, say so instead of padding the list.

## Deliverable format

Use `references/output-template.md`.

Also include:

- `Signal contract`
- `Query set`
- `Run config`
- `Goodput`
  - `query count`
  - `seed count`
  - `raw results`
  - `dated evidence`
  - `candidate companies`
  - `goodput targets`
  - `enriched targets`
  - primary failure mode
- `Targets`
- `LinkedIn resolution`
- `Memory updates`
- `Next moves`

## Done when

- The signal question is explicit.
- The match rule is explicit.
- The query families are distinct enough to test.
- The final targets are ranked by evidence strength, not filler quantity.
- Each target has a domain or a stated resolution gap.
- Every non-obvious claim is backed by a source or labeled as an inference.
