# Query archetypes

Use the closest archetype first. Start with the minimum number of query families that can prove or disprove the signal.

## 1) `ma_rationalization`

Use when the signal is about mergers, acquisitions, acquired assets, or post-deal integration pressure.

### Default query families

- `direct_news`
  - `(acquires OR acquisition OR merger OR "acquired assets") after:YYYY-MM-DD`
- `integration_pressure`
  - `(acquires OR acquisition OR merger) ("systems integration" OR "vendor consolidation" OR "vendor rationalization" OR "stack consolidation") after:YYYY-MM-DD`
- `press_release`
  - `site:businesswire.com OR site:globenewswire.com OR site:prnewswire.com (acquires OR acquisition OR merger) after:YYYY-MM-DD`
- `company_resolution`
  - `site:linkedin.com/company "<company name>"`
  - `"company name" official site`

### Notes

- The likely target is usually the acquirer or merged entity, not the publisher.
- If the result is only on a publisher domain, resolve the company identity before counting it.

## 2) `leadership_change`

Use when the signal is about a new executive, role change, or leadership turnover.

### Default query families

- `direct_news`
  - `("appointed" OR "joins as" OR "named" OR "new chief") after:YYYY-MM-DD`
- `role_specific`
  - `("chief information officer" OR "vp operations" OR "head of procurement") ("joins" OR "appointed") after:YYYY-MM-DD`
- `company_resolution`
  - `site:linkedin.com/company "<company name>"`
  - `site:linkedin.com/in "<company name>" "<title>"`

## 3) `funding_or_expansion`

Use when the signal is about new funding, expansion, new market entry, or scale transition.

### Default query families

- `direct_news`
  - `("raises" OR funding OR expansion OR "opens" OR "launches") after:YYYY-MM-DD`
- `operator_pressure`
  - `("raises" OR expansion) ("operations" OR infrastructure OR procurement OR compliance) after:YYYY-MM-DD`
- `company_resolution`
  - `site:linkedin.com/company "<company name>"`
  - `"company name" official site`

## 4) `generic_binary_signal`

Use when no better archetype fits.

### Default query families

- `direct_signal`
  - `"<signal phrase>" after:YYYY-MM-DD`
- `signal_plus_offer`
  - `"<signal phrase>" "<offer-relevant term>" after:YYYY-MM-DD`
- `resolution`
  - `site:linkedin.com/company "<company name>"`
  - `"company name" official site`

## Time rules

- For exact windows such as `last 90 days`, prefer `after:YYYY-MM-DD`.
- Use `tbs` only as a coarse helper. Do not treat it as the sole proof of exact recency.

## Stop-loss rules

- If the first pass returns only publishers, trend articles, or generic category pages, tighten the query before spending more.
- If a signal cannot produce named entities from search results, it is not yet operational enough for target discovery.
