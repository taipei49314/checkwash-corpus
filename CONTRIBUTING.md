# Contributing

This repository collects **real** measurements for checkwash. A
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

## Division of labor (two agent sessions, one human)

As of 2026-09-01 two agent sessions work these repos concurrently. The
split, so records stop eating each other:

**Engine side — Claude Code session `desktop-dd`, repo
`taipei49314/checkwash`:**

- Detector rounds and releases. Next: issue #53 (phantom unit-identity
  family) → v0.2.2. Every checkwash Release triggers this repo's watcher
  ledger sweep; every main push triggers a smoke — releases are the
  hand-off signal, cut them deliberately.
- **All adjudication verdicts** (`adjudication/*.json`). One rater across
  every dataset — the 74-block external run, wave-0 reconciliation,
  wave-1 blocks — so labels stay comparable.

**Corpus side — the session that built this repo:**

- Harness, ledger, `validate`/`status`/`fetch`, `tools/`, the clone
  estate (great_expectations repair, wave 2), census, PR harvest.
- Sweep execution, including watcher-triggered re-sweeps on new
  Releases.
- Quarantine curation (`records/incoming/`) — always with a META, as
  done for the 2026-09-01 typer record.

**Both sides:**

- A sweep record must carry `engine.asset` + `engine.sha256` (the
  harness bakes it in now); `validate` gates the sweep + adjudication
  pair.
- Never `git clean` or delete untracked files while the other session
  may be mid-write; quarantine only records that fail `validate`, and
  leave a META saying why.
- Coordination lives in commits and these docs; anything urgent routes
  through the human.
