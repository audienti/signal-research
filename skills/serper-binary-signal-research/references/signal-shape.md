# Signal shape

Use this shape whenever the user gives a yes-or-no research question.

## Required fields

- `name`: short label for the signal
- `question`: the externally checkable yes-or-no question
- `scope`: `company`, `person`, or `both`
- `why_it_matters`: why this signal matters to the offer
- `match_rule`: what counts as a real match
- `observation_methods`: where to look
- `archetype`: the closest query pattern family

## Observation methods

Each observation method should include:

- `surface`: one of `google-search`, `google-news`, `company-site`, `linkedin`, `manual`, or `other`
- `query`: the actual query
- `notes`: what the search is supposed to prove

## Good signal example

```json
{
  "name": "Recent M&A pressure",
  "question": "Has the company acquired another company or assets in the last 90 days?",
  "scope": "company",
  "why_it_matters": "Recent M&A often creates integration, stack overlap, and vendor rationalization pressure.",
  "match_rule": "Count it only if there is a dated announcement, credible news result, or company press release from the last 90 days.",
  "observation_methods": [
    {
      "surface": "google-news",
      "query": "(acquires OR acquisition OR merger OR \"acquired assets\") after:2026-03-20",
      "notes": "Find dated M&A activity."
    },
    {
      "surface": "linkedin",
      "query": "site:linkedin.com/company \"Company Name\"",
      "notes": "Resolve the LinkedIn company URL after the company is shortlisted."
    }
  ],
  "archetype": "ma_rationalization"
}
```

## Bad signal example

Bad:

- "They look interesting"
- "Maybe growing fast"
- "Probably needs this"

Those are not signals. They are guesses.

## Match rules

Write the match rule so another agent can reject weak evidence.

Good match rules usually constrain one or more of:

- recency
- source type
- role relevance
- minimum specificity
- whether the evidence names the company directly

Examples:

- "Count only evidence from the last 90 days."
- "Do not count trend pieces that do not name a company."
- "Do not count generic growth language without a concrete operating event."
