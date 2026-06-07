# Output template

Use this default markdown structure in chat unless the user asks for JSON or a file artifact.

## Thesis

- `Offer:` what is being sold
- `Premise:` one-sentence prediction
- `Best current signal pattern:` the strongest recurring pattern you found

## Signals

For each signal:

- `Signal:` short name
- `Question:` the checkable question
- `Scope:` company, person, or both
- `Match rule:` what counted

## Ranked companies

For each company:

### `<rank>. <company name>`

- `Why it matches:` one short paragraph
- `Confidence:` high, moderate, low, or unknown
- `Signal evidence:`
- `Source 1:` url + what it proved
- `Source 2:` url + what it proved
- `LinkedIn company:` url if found

`People`

- `<person name>`, `<title>`
- `Why relevant:` direct reason tied to premise or signal
- `LinkedIn:` url
- `Confidence:` high, moderate, low, or unknown

## Gaps

- What is still unverified
- Which companies look tempting but did not clear the threshold
- Which buyer roles were plausible but not proven

## Next move

- The sharpest next search or validation step if the user wants another pass
