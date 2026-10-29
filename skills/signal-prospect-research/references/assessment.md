# Score prospect fit

Use `scripts/score.mjs` to calculate a 0–100 fit score, not a purchase probability. The agent judges the evidence against the selected experiment and supplies bands with short reasons and source URLs. Code calculates the score and applies the workspace cutoff. Do not ask the operator to approve routine fit decisions.

| Dimension | Bands and points |
| --- | --- |
| Company, 25 | match 25; plausible 18; unknown 5; mismatch 0 |
| Target role, 30 | target 30; adjacent 15; unknown 5; unrelated 0 |
| Signal relevance, 30 | direct 30; adjacent 20; weak 10; none 0 |
| Evidence, 15 | corroborated 15; primary 10; weak 5; none 0 |

Company match means the stated audience criteria are supported. Plausible means broad audience fit with noncritical uncertainty. Do not invent hard size limits from words like mid-market. Role match means membership of a defined target role family; exact title wording is unnecessary. Relevance measures how likely this role is to know about the specific signal, not seniority. Evidence evaluates the source support and recency for those judgments. Existing tooling is context for the learning question, not automatic disqualification.

An explicit company mismatch, unrelated role or no signal relevance gives an overall score of zero. Missing or malformed assessments are unscored, never automatically advanced even at cutoff zero. A cutoff of zero intentionally admits every valid scored record, including zero fits. At or above the cutoff advances to conversation preparation. Below it retains the prospect without progressing. Changing the cutoff reevaluates existing scores without deleting records. Default cutoff is 70, a starting operating policy, not a calibrated predictor.

Input: `rubricVersion: "fit-v1"`, `experimentId`, `companyId`, `sources` (HTTP URLs), plus `company`, `role`, `relevance`, `evidence`, each with `band` and `reason`. Run `node scripts/score-cli.mjs` with JSON `{ "assessment": ..., "cutoff": 70 }` on stdin. In Exo save the input as person field `prospectScoring` through records. Read the person API's `scoring` result for the current cutoff, disposition and next action. Do not persist a second authoritative advance flag that can go stale after settings change.

The limit of five prospects per company is separate from score and is a maximum, never a minimum company headcount or a quota. Routine uncertainty is reflected in the score. Research again only for decision-relevant gaps. Advance means ready for the next preparation step, not permission to contact or proof of internal pain.
