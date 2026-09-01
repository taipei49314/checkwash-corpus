# checkwash-corpus

The pile of real git history we point [checkwash](https://github.com/taipei49314/checkwash) at.

This is not the engine. It is the ledger of catalogs, recorded sweeps, and
harvested PRs. Third-party source trees live in `clones/` on disk and are
never committed. See [SPEC.md](SPEC.md).

The six-repo false-positive set cannot see mocking, unittest dialect, or
JS/TS oracles. Later waves exist to close those holes.

Latest round (2026-09-01): [REPORT.md](REPORT.md) — wave 0 on Release
`checkwash.pyz` v0.2.8 still 42/1800 at the published pins; field-run
`external-2026-09-01` is a separate copied ledger (74/2300 on v0.1.49
`greenwash.pyz`, not a v0.2.8 number).

```
$ python -m corpus status
wave0-published-fp       6/6 catalogued; … 6 sweeps …
wave1-mock-power        20/20 catalogued; …
wave2-js-oracle          0/3 catalogued, 3 planned; …
external-2026-09-01      field-run 13 sweeps, 13 adjudicated; 74/2300 blocked
```

## What is in here

| wave | sources | question it can answer |
|------|---------|------------------------|
| **wave0-published-fp** | attrs, click, flask, httpx, rich, starlette | Reproduce the published 1800-commit human FP numbers. Point `checkwash bench --corpus clones` at it. |
| **wave1-mock-power** | 20 permissive Python repos from [corpus-expansion.md](https://github.com/taipei49314/checkwash/blob/main/benchmarks/corpus-expansion.md) | Is "once in 1800" a property of test-tampering or of six libraries that rarely stub anything? |
| **wave2-js-oracle** | axios, express, vitest (planned) | T3.1 JS/TS matcher weakenings. Not fetched until that round. |

Plus, without any clone:

- `records/prs/` — harvested merged PRs that actually touch test files
- `records/incoming/` — drop-box for a real agent diff (see that README)

## Install the tools

Python 3.11+, git, and `gh` (for PR harvest). Zero runtime dependencies.

```bash
git clone https://github.com/taipei49314/checkwash-corpus
cd checkwash-corpus
python -m pip install -e .          # provides the `corpus` command
# or just: python -m corpus …
```

## Collect

```bash
# 1. Clone wave 0 (small) so checkwash bench can see the published pins.
python -m corpus fetch --wave wave0-published-fp

# 2. Measure whether the clone has the power the rule needs.
python -m corpus census --wave wave0-published-fp

# 3. Harvest real merged PRs that touch tests (GitHub API, no clone required).
python -m corpus harvest-prs --wave wave0-published-fp --per-repo 15

# 4. Wave 1 is large. Depth 400, tens of GB, a round of its own.
python -m corpus fetch --wave wave1-mock-power
python -m corpus census --wave wave1-mock-power

# 5. Sweep — pin a Release zipapp, not an editable checkout.
# Latest asset is checkwash.pyz (greenwash.pyz exists only on ≤v0.1.49).
python -m corpus sweep --wave wave0-published-fp --engine checkwash.pyz
```

Point the engine at this cache:

```bash
export GREENWASH_CORPUS=/path/to/checkwash-corpus/clones
checkwash bench --corpus "$GREENWASH_CORPUS"
```

The env var is still `GREENWASH_CORPUS` (compatibility). Or clone this
repository as a sibling named `greenwash-corpus` and put the wave-0
checkouts at that root (the layout `checkwash bench` still looks for).
`python -m corpus fetch --wave wave0-published-fp --layout bench` does that
when the repo itself is checked out as `greenwash-corpus`.

## What we will not do

- Vendor apache/airflow or huggingface/transformers into git.
- Publish a wave-1 false-positive rate before a census of that wave.
- Mix wave 0 and wave 1 in one headline number.
- Fold the 74/2300 field-run into a wave0/wave1 headline. That run is v0.1.49.
- Treat a harvested PR patch as a checkwash verdict. The engine has to say it.

## Layout

```
catalog/CATALOG.json     inclusion list (frozen probes, waves, pins)
records/sweeps/          checkwash sweep JSON, one file per source
records/field-runs/      copied external field-runs; not a wave
records/census/          power counts at a named revision
records/prs/<id>/        harvested test-file patches from GitHub
records/incoming/        agent-diff drop-box
adjudication/            human FP/spec-correct split, after a sweep
clones/                  gitignored cache
src/corpus/              stdlib CLI
```

License: Apache-2.0 (this repository's tools and records). Third-party
projects keep their own licenses; we do not re-ship their trees.
