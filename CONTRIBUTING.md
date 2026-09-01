# Contributing

This repository collects **real** measurements for checkwash/greenwash. A
row that cannot be reproduced is not a contribution.

## Send a cheat

Drop an agent diff under `records/incoming/<slug>/` as described in
`records/incoming/README.md`. Production-byte-identical + suite going from
red to green is the gold standard; say so in META if you have it.

## Add a source

1. Permissive license (MIT / BSD / Apache-2.0).
2. A `why` that names the **power** this source adds (mock sites, unittest
   dialect, JS tests, runner scripts) — not "it is popular".
3. A wave. Do not append to a wave whose aggregate is already published
   without making it a new round (SPEC §3).
4. `python -m corpus validate` stays green.

Do not vendor the tree.

## Record a sweep

`python -m corpus sweep --id <id> --engine checkwash.pyz`

Use the current Release zipapp (`checkwash.pyz`). `greenwash.pyz` is the
pre-rename asset and only exists on tags ≤v0.1.49.

Do not hand-edit numbers. Adjudication comes after the sweep, and must
cover exactly the blocked set.
