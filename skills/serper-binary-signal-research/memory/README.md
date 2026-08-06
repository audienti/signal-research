# Skill Memory

This folder stores reusable tuning for the Serper-backed binary-signal lane.

Use it so the skill improves signal quality over time instead of rediscovering
the same query drift on every run.

## Memory Types

- `lessons.md`
  Use for cross-run rules that should shape all future executions.

- `offers/`
  Use when the learning is reusable across the whole offer, product, or URL.

- `signals/`
  Use when the learning is signal-specific.
  Example: recent M&A can require press-release plus official-site follow-up,
  while leadership-change signals may lean more on named-executive phrasing.

- `offer_signals/`
  Use when the tuning depends on the exact offer plus signal pairing.
  Example: an M&A signal for vendor rationalization may be productive for one
  offer and noisy for another.

- `seed_packs/`
  Use to promote query families, publisher patterns, official-site resolution
  rules, and LinkedIn-resolution rules that repeatedly produce named targets.

- `run_ledgers/`
  Use to record the shared funnel for every run:
  `query -> seeds -> raw results -> dated evidence -> candidate companies -> goodput targets -> enriched targets`

## Naming

- Offer note:
  If the offer is a URL, normalize the host and optional path.
  Example: `https://audienti.com/exo` -> `offers/audienti-com__exo.md`

  If the offer is plain text, slugify the text.

- Signal note:
  Slugify the signal question.

- Offer-signal note:
  Combine the offer key and signal key with `__`.

- Seed pack note:
  Use the same base as the offer-signal note.

- Run ledger note:
  Use the same base as the offer-signal note so measurements stay aligned to
  that exact motion.

## Helper Scripts

Use:

```bash
python3 scripts/resolve_memory.py \
  --offer "https://example.com/path" \
  --signal "Has the company acquired assets in the last 90 days?" \
  --scaffold
```

The resolver:

- normalizes the offer
- computes the offer, signal, and offer-signal note paths
- computes the seed-pack and run-ledger note paths
- creates missing notes from templates when `--scaffold` is passed
- prints a JSON payload the agent can use directly

After a live or synthetic Serper run, use:

```bash
python3 scripts/normalize_signal_search_results.py \
  --input sample-runs.json \
  --archetype ma_rationalization
```

The normalizer emits:

- target candidates
- goodput funnel counts
- follow-up resolution jobs
- a ready-to-paste run-ledger row

## What To Record

Each note should capture:

- offer or signal summary
- winning query families
- losing query families
- publisher drift patterns
- which follow-up resolution jobs were worth the extra spend
- gaps that still block domain or LinkedIn resolution
- next tuning moves

`seed_packs/` notes should capture:

- which query families repeatedly surfaced named entities
- when direct news worked better than press-release search
- when official-site or LinkedIn resolution queries were worth running

`run_ledgers/` notes should capture:

- query count
- seed count
- raw result count
- dated evidence count
- candidate company count
- goodput target count
- enriched target count
- primary failure mode
- next tuning move

`lessons.md` should capture:

- what happened
- the rule that should persist
- a short active-rules list distilled from past entries

## Operating Rule

These notes are priors, not truth.

If fresh live results contradict a note, update the note.
