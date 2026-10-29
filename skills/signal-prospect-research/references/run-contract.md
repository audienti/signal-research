# Run contract

Keep a caller-owned `run.json` plus immutable evidence files. JSON, not a database, is sufficient. A run contains:

```json
{
  "version": 1,
  "asOf": "2026-10-29T12:00:00Z",
  "mode": "native",
  "brief": {
    "offer": "Full offer and context",
    "companyCriteria": {"business": "B2B software", "size": "51–200 employees"},
    "roleCriteria": {"role": "Current sales manager; exclude founders and VPs"},
    "targetCount": 10, "peoplePerCompany": 5
  },
  "config": {
    "topic": "Companies building their sales team",
    "scope": "company", "logic": "AND", "filters": [],
    "signals": [
      {"id": "hiring", "scope": "company", "question": "Is the company currently hiring account executives?", "matchRule": "Live employer-owned vacancy for an AE, with an active application path and no closure evidence", "maxObservationAgeDays": 30},
      {"id": "leader", "scope": "company", "question": "Did the company appoint a sales leader in the last 120 days?", "matchRule": "Dated announcement explicitly identifies appointment and company", "maxObservationAgeDays": 30, "eventSince": "2026-07-01", "eventUntil": "2026-10-29"}
    ]
  },
  "requirements": {"companyCriteria": ["business", "size"], "roleCriteria": ["role"]},
  "companies": [], "people": [], "calls": [], "queue": [],
  "prior": {"complete": false, "aliasesResolved": false, "personIds": []}
}
```

Replace the illustrative dates and all example criteria. `requirements` must contain every material criterion/exclusion from the brief, with its ID and full definition retained in `brief`. All questions in one config share scope. For mixed scopes run separate company/person configs and explicitly join each person only to their verified employer; do not combine unrelated entities.

Each company row: `{ "subject": {"id":"company:example.com","scope":"company","name":"Example"}, "signals":[], "fit":[] }`.

Each person row: `{ "person":{"id":"https://www.linkedin.com/in/exact-person","scope":"person","companyId":"company:example.com","name":"Name"}, "signals":[], "fit":[] }`. For company scope the company's signals are used; for person scope use only that person's signals. Source-backed person aliases may appear on `person.aliases`; do not resolve identities by name. Preserve case for opaque provider IDs; do not assume a vanity URL and opaque ID are different people.

A signal evidence record contains:

```json
{
  "targetId": "company:example.com", "scope": "company", "questionId": "hiring",
  "answer": true, "evidenceKind": "explicit_positive", "sourceRelation": "first_party",
  "sourceUrl": "https://example.com/careers/ae", "access": "opened",
  "observedAt": "2026-10-29T12:00:00Z", "eventAt": null,
  "summary": "What this exact source establishes, including ownership and open-state checks",
  "quote": "Exact decisive source text", "rawEvidenceFile": "evidence/source.json",
  "acquisitionMode": "native", "callId": "call-1"
}
```

`sourceRelation` is first_party/filing/third_party. A provider response can be opened evidence when its actual returned fields are inspected; identify that response and underlying URL/source separately. Search snippets remain `access: "snippet"` and discovery leads. Explicit false requires `evidenceKind: "explicit_negative"` and `coverage` explaining why it answers the whole question. For a windowed negative, provide `coverageSince`/`coverageUntil` covering the question interval. A narrow counterexample does not prove a broad negative. Unsupported/missing evidence gives null; no fabricated false row is needed.

Each fit record: `{ "id":"size", "targetId":"company:example.com", "status":"met", "reason":"Exact evidence against the full criterion", "sources":[{"url":"https://example.com/about", "access":"opened", "observedAt":"2026-10-29T12:00:00Z", "sourceKind":"current_page", "rawEvidenceFile":"evidence/about.json"}] }`. `status` is met/not_met/unknown. For a person include an `employment` fit record with `companyId`, plus every role requirement. The helper always requires employment. `current_page` means an inspected live source that asserts current state, not an old page fetched now. For historical sources set `publishedAt` instead; the helper requires a date within 30 days, while the agent must still check meaning and conflicts. Adjust question freshness explicitly; do not silently loosen fit freshness or criteria to pass a case.

Company filters use `{ "kind":"company_name|company_url|linkedin_company_url", "value":"caller input", "resolution":{...} }`. Resolution includes `status: "resolved"`, canonical `companyId`, opened current `sources` with URL/date/summary and:

- Name: `matchedNames` explicitly evidenced as this company; reject ambiguous names.
- Website: official domain; for regional aliases include `aliasDomains:[{domain,canonicalDomain,sources}]` backed by explicit corporate identity links, not a self-attested description on an unrelated site.
- LinkedIn: `linkedinUrls` containing normalized `https://www.linkedin.com/company/slug`, plus `websiteDomain` bound by the opened company's website field or reciprocal official link.

Unproven regional/parent/domain equivalence must remain unresolved. The helper checks record shape, not identity truth; it will trust a false annotation. Agent source review is mandatory before recording `resolved` or `current_page`.

Each queue item records `{targetId, stage, status, nextAction, attempts, lastCallId}`. Stages: identity, company_fit, signals, role_search, employment, qualification. Status: pending, complete, exhausted, blocked. Every unresolved candidate has a named missing fact and next action. Every call records `{id, mode, tool, purpose, inputSummary, startedAt, recordedAt, outcome, evidenceFiles, cost, credits}`; preserve null unknown costs and failed calls. `recordedAt` is the UTC time evidence was captured/received, not a later replay time. The source audit requires observation time within one minute of the capture receipt, using the helper's `fetchedAt` where available. Save after each material transition. Resume the queue, revalidating expired evidence. Do not add a scheduler.

Optional deterministic replay:

```sh
node SKILL_DIR/scripts/evaluate-run.mjs RUN/run.json > RUN/results.json
```

Every opened signal, fit source and filter-resolution source must include `quote`, `rawEvidenceFile`, `acquisitionMode` (`native` or `credits`) and `callId`. The CLI checks file existence within the run directory, quote presence in saved text/JSON and binding to a recorded call whose `evidenceFiles` includes that file. Dated events also require a `dateQuote` present in the raw evidence; the agent must verify that its meaning/date equals `eventAt`. Public HTML helper output is an appropriate saved source: it preserves text and extracted job descriptions, plus a hash and adjacent raw HTML. Saved-HTML mode makes no live-fetch claim; carry its original capture receipt separately and do not invent an observation time from the parse time.

The output contains company signal matrices, person qualification, novelty and remaining queue. It never upgrades missing evidence or performs semantic fact checking. Check dates, identity and entailment yourself. The exported pure `evaluateRun` function is for controlled logical tests; use the CLI for the source audit. Rejected evidence counts and unknown criteria remain visible. With unresolved prior identities, `newCount` stays null. Existing benchmark saves, company signal matches, provisional people and new qualified people are separate metrics. The agent enforces requested count and people-per-company limits while draining the queue; the checker does not truncate already collected evidence.
