# Signal Prospect Research

Version 0.4.0 researches configured Boolean questions, verifies company and role fit,
and returns sourced prospects with unresolved evidence kept explicit.

Install `signal-prospect-research` from the Audienti marketplace, or copy
`skills/signal-prospect-research` into your agent’s skills directory.

Native web research is the baseline; an optional Treg recipe supports authorized
credit-tool retrieval. No provider account or Exora connection is required for the
baseline. This package does not send outreach, install a scheduler or deploy an app integration.

The run contract supports company/person scopes, AND/OR questions, company filters,
current employment and evidence-backed identity. The deterministic evaluator and
source audit check structure, binding and quote presence; the agent must judge
whether evidence actually supports a claim. Unknown evidence is not false.

The legacy score helpers and references are retained from the author’s unpublished
local lineage and are first published in this release.
They use their separate contract and are not substitutes for the new Boolean run
evaluator. The skill’s linked run contract is the guide for new research.

Validation:

```sh
node --test test/*.test.mjs
python3 -m unittest discover -s test -p 'test_*.py'
```

No matched-effort yield improvement, daily capacity, production parity or complete
cost-efficiency claim is made by this release. Private live experiments are not distributed.

Claude Code installation:

```sh
claude plugin install signal-prospect-research --marketplace audienti/plugins
```

Codex installation (after adding the Audienti marketplace):

```sh
codex plugin add signal-prospect-research@audienti
```
