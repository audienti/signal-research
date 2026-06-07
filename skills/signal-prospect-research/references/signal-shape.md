# Signal shape

Use this shape whenever the user gives a premise or a loose description of the kind of company they want.

## Required fields

- `name`: short label for the signal
- `question`: the externally checkable question
- `scope`: `company`, `person`, or `both`
- `why_it_matters`: why this signal supports the premise
- `match_rule`: what counts as a real match
- `observation_methods`: where to look

## Observation methods

Each observation method should include:

- `surface`: one of `company-site`, `news`, `google`, `sales-navigator`, `linkedin`, `manual`, `other`
- `query`: the actual query or lookup approach
- `notes`: what you expect to find there

## Good signal example

```json
{
  "name": "Security expansion pressure",
  "question": "Is there recent public evidence that the company is expanding security tooling or governance?",
  "scope": "company",
  "why_it_matters": "A visible security expansion usually means new evaluation, integration, or operational pressure.",
  "match_rule": "Count it only if there is a recent hiring signal, product/security announcement, compliance push, or public operating change from the last 6 months.",
  "observation_methods": [
    {
      "surface": "company-site",
      "query": "site:company.com security compliance trust",
      "notes": "Trust center, compliance pages, security product claims, new programs."
    },
    {
      "surface": "news",
      "query": "\"Company Name\" security OR compliance OR governance",
      "notes": "Funding, breach response, platform expansion, regulatory pressure."
    },
    {
      "surface": "sales-navigator",
      "query": "Search for security leadership and recent role changes",
      "notes": "Validate whether the likely buyer set exists and looks active."
    }
  ]
}
```

## Bad signal example

Bad:

- "They seem like a fit"
- "Fast-growing company"
- "Probably needs this"

Those are not signals. They are guesses.

## Scope rules

- `company`: the evidence is about the company itself
- `person`: the evidence is about a specific stakeholder
- `both`: either kind can support the premise, but keep them separate in the final writeup

## Match rules

Write the match rule so another agent can reject weak evidence. Good match rules usually constrain one or more of:

- recency
- source type
- role relevance
- minimum specificity

Example:

- "Count only evidence from the last 90 days."
- "Count hiring only when the role maps to the target function."
- "Do not count generic growth language without a concrete operating change."
