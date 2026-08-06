# Serper search notes

This skill uses Serper's Google endpoints as the primary search layer.

## Current request shape

This request shape is based on:

- the current Serper homepage, which still presents the product as a real-time Google Search API with country and language customization
- working internal Serper usage already present in the v10 codebase and test cassettes

The public homepage does not spell out every request field, so the exact body keys below are partly inferred from working code and recorded requests.

## Endpoint

- Base URL: `https://google.serper.dev`
- Search endpoint: `/search`
- News endpoint: `/news`

## Headers

- `Content-Type: application/json`
- `X-API-KEY: <SERPER_API_KEY>`

## Supported body fields in this skill

- `q`
- `hl`
- `gl`
- `page`
- `tbs`

## Time filter rule

- If `tbs` is supplied as `d`, `w`, `m`, or `y`, this skill converts it to `qdr:<value>`.
- For exact windows like `last 90 days`, put the absolute date in the query with `after:YYYY-MM-DD`.

## Response fields used by this skill

From the response, this skill uses:

- `organic`
- `news`
- `knowledgeGraph`
- `searchParameters`

From each result item, this skill uses:

- `title`
- `link`
- `snippet`
- `date`
- `source`
- `position`

## Good usage pattern

1. Run named-entity discovery queries.
2. Normalize and dedupe results.
3. Resolve the official domain and LinkedIn company URL only for shortlisted names.

Do not start with LinkedIn URL resolution before a named company candidate exists.
