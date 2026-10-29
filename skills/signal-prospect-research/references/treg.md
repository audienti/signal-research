# Optional Treg execution recipe

Use when Treg tools or an authenticated `treg` CLI are available and the caller wants credit-assisted research. Keep native-only mode available. Treg injects provider credentials server-side; this skill needs no provider keys and no application integration. Discover/read the current schema and price before calling: endpoint availability, parameters and billing can change.

## Capability discovery and execution

Prefer the host's connected `catalog_search`, `catalog_get` and `call` tools. For the CLI, the equivalent discovery commands are:

```sh
treg catalog search "search linkedin people keyword current company"
treg catalog get harvestapi.linkedin.profile.search
treg catalog get fetchinio.linkedin.user.profile
treg catalog get treg.linkedin.company.profile
```

These are observed working endpoints, not mandatory vendors. If the connected execution token fails but the existing CLI is authenticated, use that CLI without copying credentials, changing account configuration or asking for a provider key. If neither works, continue native and report the access gap. Never top up or change credentials as part of research without authorization.

On the verified schemas (2026-10-29), role-scoped search uses a GET with `currentCompany` (exact LinkedIn company URL or numeric ID), `title`, and `page`. Do not put job-title keywords in `search`, which is described as a name search. Supply only declared fields. Example invocation, replacing placeholders:

```sh
treg call harvestapi.linkedin.profile.search \
  --query currentCompany=https://www.linkedin.com/company/COMPANY_SLUG/ \
  --query 'title=Account Executive' --query page=1 \
  --header 'X-Treg-Route-Max-Cost: 0.01' \
  --header 'X-Treg-Route-Strict-Filters: 1' --json
```

Inspect `result.elements`, pagination, body status/error and returned query/company IDs. Search rows are candidates, not verified current roles. A headline can differ from the current job. A successful HTTP status or a name alone is not a fit result. Freeze candidate ordering/selection before looking up profiles when comparing procedures; preserve unexamined rows as pending, not rejected.

Title search recall is incomplete: in the live probe, `founder` returned a cofounder but missed the known `Cofounder & CEO`. Retain known exact identities and test title variants/role families when expanding coverage; one empty or short result set is not proof of exhaustion.

Profile lookup on the observed Fetchin schema:

```sh
treg call fetchinio.linkedin.user.profile \
  --query profileUrlOrUrn=https://www.linkedin.com/in/PERSON_SLUG \
  --header 'X-Treg-Route-Max-Cost: 0.01' --json
```

Inspect the returned exact profile URL/public identifier, `currentPosition`, `experiences`, company URL/ID, title, start/end dates and current flags. Bind the company URL/ID to the official domain before using it. A profile search can match past titles; only the target-company current experience supports employment. Retain contradictions such as an old employer whose date still says Present despite a false current flag. Do not assume exclusive employment. Responsibilities may establish a genuine role equivalent; neither a vague headline nor a title substring establishes seniority or overrides exclusions.

Capture the current experience's `dateRange` as well as its title and company binding in source quotes, and inspect its current/end-date fields. A cofounder title alone does not establish individual revenue authority; preserve any caller-approved small-company proxy and flag contrary or ambiguous role evidence rather than silently changing the criteria.

The routed company endpoint takes POST JSON `{ "linkedin_url": "https://www.linkedin.com/company/COMPANY_SLUG/" }`. Inspect both normalized `output` and provider-native `raw`. The normalized result can omit company identity or website fields needed for qualification. Preserve exact website/company IDs, employee **band**, and associated-member count as separate fields. Missing/masked required fields trigger one relevant alternate capability/provider or remain unknown; repeatedly receiving a valid response without the required fact is not success.

## Cost and evidence

Before spending, establish a bounded call/credit allowance within the caller's authorization. Do not treat the account balance or another agent's budget as your campaign allocation. The observed profile call cost was $0.0015; profile search catalog price was $0.004 but actual receipts in this probe were $0.002; a routed company lookup charged $0.001. These are examples, not guaranteed future rates. Tell the caller the current catalog price for calls over one cent.

Routed calls may bill unsuccessful child attempts. Set a route ceiling when supported, inspect `served_by`/`tried` and preserve child receipts. In the observed CLI wrapper those routing fields live under `result._treg`; the top-level `_treg` carries call ID, HTTP status and charge. The example ceiling is per call, not a total budget; the agent must also track total spend and unknown reservations. `X-Treg-Route-Strict-Filters: 1` requests rejection of unsupported routed filters; still check the returned data and actual schema.

Save the exact request, response, timestamps and `_treg` receipt before annotating evidence. CLI `_treg.charged_micro / 1000000` is the actual gateway charge; MCP may expose `cost_usd`. Preserve explicit zero, failed attempts and null unknown charges. On a timeout use the supported idempotency mechanism where available, or inspect the receipt before retrying; do not silently pay twice. Model/native-search costs remain separate and may be unknown.

Map inspected response fields into the normal run contract with `acquisitionMode: "credits"`, `access: "opened"` (provider response inspected), exact source profile/company URL, quote, raw response file, call ID and observation timestamp. This does not mean the public profile body was opened in a browser. Preserve provider identity and unknown underlying data-update time. A run using native signal evidence plus credit profile facts is **hybrid**; do not report those prospects as native-only.

## What this recipe proves

The tested useful change was company-and-role discovery plus exact profile/company verification after native signal discovery. It increased verified coverage of a bounded set of existing company cases, including re-verification of people already in V10. Compare exact identities against the caller's prior cohort before reporting additions: record known matches, unseen URLs and unresolved aliases separately. An unseen URL alone does not establish a new person. This does not prove equal-effort full-discovery throughput, daily capacity, V10 parity or cohort novelty. Keep those metrics separate and continue to test the native option.
