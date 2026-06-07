# Tool recipes

Use the strongest live tool path that exists in the current run. Do not claim access you do not actually have.

## 1) Unipile account discovery

Use this first when `mcp__unipile` is available.

Goal:

- find the live LinkedIn account
- confirm whether Sales Navigator is available on that account

Request shape:

```json
{
  "harRequest": {
    "method": "GET",
    "url": "https://<your-unipile-base>/api/v1/accounts",
    "headers": [
      { "name": "accept", "value": "application/json" }
    ]
  }
}
```

Look for:

- `type: "LINKEDIN"`
- `connection_params.im.username`
- `connection_params.im.premiumFeatures`

If the endpoint returns `errors/no_client_session`, do not assume the default Unipile server is correct. Resolve the active backend before concluding the connector is down.

## 2) Unipile Sales Navigator people search

Use when you already know the company and want likely buyers.

Request shape:

```json
{
  "harRequest": {
    "method": "POST",
    "url": "https://<your-unipile-base>/api/v1/linkedin/search",
    "queryString": [
      { "name": "account_id", "value": "<linkedin-account-id>" },
      { "name": "limit", "value": "25" }
    ],
    "headers": [
      { "name": "accept", "value": "application/json" },
      { "name": "content-type", "value": "application/json" }
    ],
    "postData": {
      "mimeType": "application/json",
      "text": "{\"api\":\"sales_navigator\",\"category\":\"people\",\"company\":{\"include\":[\"ExampleCo\"]},\"role\":{\"include\":[\"Chief Revenue Officer\",\"VP Marketing\",\"Head of Demand Generation\"]},\"seniority\":{\"include\":[\"cxo\",\"vice_president\",\"director\"]}}"
    }
  }
}
```

Rules:

- Start narrow.
- Use real titles from the motion, not a giant kitchen-sink title list.
- Tighten by company, seniority, geography, and function before widening keywords.

## 3) Unipile company profile lookup

Use after you have a public identifier or company name you trust.

Request shape:

```json
{
  "harRequest": {
    "method": "GET",
    "url": "https://<your-unipile-base>/api/v1/linkedin/company/<identifier>",
    "queryString": [
      { "name": "account_id", "value": "<linkedin-account-id>" }
    ],
    "headers": [
      { "name": "accept", "value": "application/json" }
    ]
  }
}
```

Useful fields:

- `profile_url`
- `website`
- `employee_count`
- `employee_count_range`
- `industry`
- `description`
- `followers_count`
- `insights`

## 4) Icypeas company and profile discovery

Use when you need clean LinkedIn URLs fast.

- One company: `company_search`
- Two or more companies with known LinkedIn URLs: `bulk_company_scraper`
- One person: `profile_search`
- Two or more confirmed profile URLs: `bulk_profile_scraper`

Use `bulk_*` when the URL list is already known. Do not waste calls one by one.

## 5) Native web research

Use web search for:

- official company pages
- trust centers
- news
- hiring pages
- funding announcements
- product launch pages
- case studies
- public social posts

Good search shapes:

- `site:company.com <signal words>`
- `"<company>" <signal words>`
- `site:linkedin.com/company "<company>"`
- `site:linkedin.com/in "<company>" "<title>"`

## 6) Fallback rules

- If Unipile is present but blocked, keep going with web plus Icypeas.
- If LinkedIn identity is uncertain, do not pretend profile data is verified.
- If company evidence is weak, stop before stakeholder bloat.
