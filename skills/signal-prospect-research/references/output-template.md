# Research handoff

Use the workspace's records when authorized. Otherwise return a concise Markdown report or requested structured format.

## Structured form

For another agent or CRM integration, return JSON with `schemaVersion: 1`,
`skill: {id: "signal-prospect-research", version: "0.4.0"}`, `briefRef` (caller
reference or null), `status` (`completed`, `partial` or `blocked`), `companies`,
`people`, `sourcesChecked`, `gaps` and `nextAction`. The company and person objects
carry the evidence described below, with local references for relationships.
Use observed provider IDs or profile URLs for identity; never names as dedupe keys.
Keep a distinct signal answer per subject and question, its evidence URLs, observed
time, event time when known and freshness decision. No result from one subject
can satisfy another subject's all rule. Missing or inaccessible evidence is unknown.

Company criteria and person-role fit remain separate arrays of criterion,
`met|not_met|unknown`, reason and evidence URLs. Retain scorer input and output
when scoring is possible; missing score prerequisites stay explicitly unscored.
Do not invent an experiment ID, company identity or source merely to run scoring.
Keep CRM persistence receipts separate from research completion. Exo's existing
record mapping and score readback remain optional host behavior.

## Experiment
Experiment reference, premise, company criteria, candidate roles, signal questions and resolved batch limits.

## Company
Identity and sources. Each material company criterion: met, not met or unknown. Each signal: question, scope, yes/no/unknown, evidence, source URL, observation date and event date if known. Counterevidence and remaining fit gaps.

## People
Name, current employer, role and supporting evidence, known profile/contact URLs, relevant signal reference, why they might know, fit verdict, confidence and uncertainties. Separate verified title from a descriptive role label. Do not assign a buying role.

## Next decision
Research complete or provisional, missing evidence that matters, question for validation, human decision if required, and saved record references. No assumption that research authorizes contact.
