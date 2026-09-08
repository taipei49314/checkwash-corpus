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
| eligibility is derived | `corpus.holdout.eligible` computes the pool from the catalog, `records/sweeps/`, `records/field-runs/`, [`spent-elsewhere.json`](spent-elsewhere.json) and earlier draws — never a hand-kept list |
| the seed is public and prior | recorded with its provenance, so the ids recompute from `(pool, seed)`; `corpus validate` re-derives them and fails if they do not match |
| predict first | the record states the expected direction against the in-sample rate before the sweep |
| one measurement | sweeping and publishing the raw block rate does not spend the set; adjudicating it does, and then those repositories are tuning corpus forever |

## Draws

| date | class | sources | commits | engine | spent |
|---|---|---|---|---|---|
| [2026-09-08](2026-09-08/DRAW.json) | held-out | airflow, bokeh, localstack, mlflow, ray, transformers | 6 × 300 = 1800 | checkwash v0.3.2 | no — stops at the raw block rate |

The 2026-09-08 draw is the first under SPEC section 10.2 rule 2. Its
denominator matches the in-sample 46/1800 on purpose, so the two rates
compare without converting either one. **Three sources are left in reserve**
(azure-cli, great_expectations, salt), and a held-out number goes stale under
rule 4 whenever detector logic changes — so the reserve is worth spending
deliberately, not on the next convenient question.

## Sweeps that happen somewhere else

[`spent-elsewhere.json`](spent-elsewhere.json) records repositories a
measurement outside this repository already swept. It exists because the first
computation of the 2026-09-08 draw got the frame wrong: the exploratory
external evaluation of 2026-09-08 had swept ten repositories on checkwash
v0.3.2 from a working directory outside every repository, leaving no trace
here, and six of them were still being counted as reserve. Any measurement run
outside this repository belongs in that file on the day it runs, or the next
draw repeats the mistake.

[spec]: https://github.com/taipei49314/checkwash/blob/main/SPEC.md
