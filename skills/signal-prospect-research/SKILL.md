---
name: signal-prospect-research
description: Turn an offer premise and signal questions into a ranked company-and-buyer target list. Use when the user asks to find companies with externally verifiable problems, identify the best-fit people at those companies, run LinkedIn or Sales Navigator research through available tools, and return evidence-backed prospects with sources.
---

# Signal Prospect Research

## Goal

- Turn a vague outbound idea into a tight research contract: offer -> premise -> signals -> companies -> people.
- Find companies showing real external evidence that the premise is live.
- Pick the smallest credible stakeholder set, starting with the most likely owner.

## Default stance

- This skill is read-only by default. Do not write to Exo unless the user explicitly asks for writeback.
- Do not invent signal matches, buyer ownership, or recency.
- Prefer a short ranked list with strong evidence over a big weak list.

## Inputs to ask for if missing

- What is the offer or product being sold.
- What is the premise. Use one sentence starting with "This offer matters when..."
- What titles, role families, or buyer functions matter most.
- How many companies and how many people per company are needed.
- Geography, industry, size, or stage constraints.

If the user gives a loose explanation instead of structured inputs, normalize it yourself before researching.

## Core model

Use this exact reasoning sequence:

1. `offer`
   - What is being sold.
2. `premise`
   - The prediction about when the offer matters.
3. `signals`
   - Externally checkable questions that would make the premise more likely true.
4. `company matches`
   - Specific companies with evidence that one or more signals are live.
5. `people`
   - The smallest credible buyer set at each matched company.

Use the signal shape in `references/signal-shape.md`.

## Workflow

### 1) Normalize the request into signal objects

For each signal, define:

- `name`
- `question`
- `scope`: `company`, `person`, or `both`
- `why_it_matters`
- `match_rule`
- `observation_methods`

Do not start searching until the signals are clear enough that two different agents would look for roughly the same evidence.

### 2) Resolve the live tool surface

Check what you can actually use in this run.

- If `mcp__unipile` is available, use it for LinkedIn account discovery and LinkedIn or Sales Navigator search.
- If `mcp__icypeas` is available, use it for LinkedIn company URL discovery, profile URL discovery, and bulk scraping.
- Use native web research for company-site, news, hiring, trust-center, funding, product, and public-social evidence.
- If the user explicitly wants Sales Navigator page inspection and a browser connector is available, use the native browser or Chrome path that is actually present. Do not fake direct Sales Navigator access from plain web search.

Use the examples in `references/tool-recipes.md`.

### 3) Run the company research loop

For each candidate company, work in this order:

1. Company site
2. News or web
3. LinkedIn company identity
4. Sales Navigator or LinkedIn search if needed

Keep only signal matches you would actually use in outreach. Drop weak decorative findings.

A usable company match needs:

- company name
- domain
- LinkedIn company URL if available
- 1 to 3 strong signal matches
- source URLs
- observed dates when available
- confidence: `high`, `moderate`, `low`, or `unknown`

### 4) Pick the buyer set

Start with the most likely primary owner, then add only the strongest adjacent operator, sponsor, evaluator, or blocker when it strengthens the case.

Selection rules:

- Tie each person back to the premise or a specific signal.
- Title alone is not enough.
- Prefer the smallest credible set.
- If the company fit is good but the buyer fit is weak, say so directly.

### 5) Verify each person

For each selected person, get:

- full name
- current title
- LinkedIn profile URL
- why they are relevant
- what evidence supports the fit
- confidence

If there are 2 or more confirmed LinkedIn profile URLs, prefer bulk scraping over one-by-one scraping.

### 6) Return a ranked output

Use `references/output-template.md`.

Default output shape:

- short thesis
- ranked companies
- per-company signal evidence
- selected people
- confidence and gaps
- follow-up search ideas only where evidence is still incomplete

## Research rules

- Company evidence comes before people hunting.
- Recent evidence beats evergreen theory.
- External verification beats category stereotypes.
- Do not present inferred issues as confirmed facts.
- Keep company-level and person-level signals distinct.
- If you cannot verify a company signal, do not smuggle it in through a person title.
- If no strong matches exist, say the motion is weak instead of padding the list.

## Deliverable format

Default: markdown in chat using the template in `references/output-template.md`.

If the user asks for machine-readable output, return JSON with these top-level keys:

- `offer`
- `premise`
- `signals`
- `companies`
- `summary`
- `gaps`

## Done when

- The premise is explicit.
- The signals are explicit and externally checkable.
- The companies are ranked by evidence strength, not by filler quantity.
- Each selected person has a real reason to be there.
- Every non-obvious claim is backed by a source or labeled as an inference.
