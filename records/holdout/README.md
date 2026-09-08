# Held-out draws

One directory per draw, named by its draw date, holding `DRAW.json`.

A held-out rate is the only number that answers "how often does checkwash
block repositories nobody tuned it on". It means that **only** if the draw
was recorded before the engine ran, so the record is committed first and the
sweep comes after. [SPEC section 10][spec] in the engine repository defines
the two classes, the eligibility rules and what spends a set.

`records/sweeps/` holds catalogued wave sweeps. `records/field-runs/` holds
copied field-run ledgers. Neither is a draw, and neither may be relabelled as
one after the fact.

## The contract

| rule | what it means here |
|---|---|
| draw before you look | `DRAW.json` lands in a merged commit before any sweep runs |
| eligibility is derived | `corpus.holdout.eligible` computes the pool from the catalog, `records/sweeps/`, `records/field-runs/` and earlier draws — never a hand-kept list |
| the seed is public and prior | recorded with its provenance, so the ids recompute from `(pool, seed)`; `corpus validate` re-derives them and fails if they do not match |
| predict first | the record states the expected direction against the in-sample rate before the sweep |
| one measurement | sweeping and publishing the raw block rate does not spend the set; adjudicating it does, and then those repositories are tuning corpus forever |

## Draws

| date | class | sources | commits | engine | spent |
|---|---|---|---|---|---|
| [2026-09-08](2026-09-08/DRAW.json) | held-out | azure-cli, localstack, mlflow, salt, scrapy, transformers | 6 × 300 = 1800 | checkwash v0.3.2 | no — stops at the raw block rate |

The 2026-09-08 draw is the first under SPEC section 10.2 rule 2. Its
denominator matches the in-sample 46/1800 on purpose, so the two rates
compare without converting either one.

[spec]: https://github.com/taipei49314/checkwash/blob/main/SPEC.md
