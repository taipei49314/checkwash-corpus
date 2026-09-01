# Adjudication

A sweep is a machine count of blocks. The false-positive split is a human
judgement of each blocked commit against the real diff.

`python -m corpus validate` refuses to treat an adjudication file as
describing a sweep unless the `(catalog_id, commit)` set matches the sweep's
`blocked_commits` exactly — the same gate greenwash's `make_results.py`
enforces.

Do not start an adjudication file until the matching sweep record exists.

Template: [TEMPLATE.json](TEMPLATE.json). It is the same per-commit method
used to reconcile wave 0 against the published 42 blocks (`false_positive` /
`spec_correct` / `unclear`, reason against the real diff, blocked set must
match the sweep exactly). Wave 1 sweeps reuse this file; do not invent a
second schema.
