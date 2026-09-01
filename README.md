# checkwash-corpus

Real-world measurement corpus for [checkwash / greenwash](https://github.com/taipei49314/greenwash).

greenwash catches diffs that tamper with the verification layer. Every number
it publishes is only as good as the history it was pointed at. The six-repo
false-positive corpus cannot see mocking, unittest dialect, or JS/TS oracles.
This repository is the place those measurements get collected.

**This clone is a ledger, not a mirror.** Catalog, recorded sweeps, censuses,
and harvested PR patches live in git. Third-party source trees live in
`clones/` on disk and are never committed. See [SPEC.md](SPEC.md).

Latest round (2026-09-01): [REPORT.md](REPORT.md) — wave 0 sweep reproduced
42/1800 against the published pins; wave 1 census is 19/20 clones.

```
$ python -m corpus status
wave0-published-fp   6/6 catalogued, 0 cloned, 0 census, 0 sweeps
wave1-mock-power    20/20 catalogued, 0 cloned, 0 census, 0 sweeps
wave2-js-oracle      3 planned (fetch with --include-planned)
```

## What is in here

| wave | sources | question it can answer |
|------|---------|------------------------|
| **wave0-published-fp** | attrs, click, flask, httpx, rich, starlette | Reproduce the published 1800-commit human FP numbers. Point `greenwash bench --corpus clones` at it. |
| **wave1-mock-power** | 20 permissive Python repos from [corpus-expansion.md](https://github.com/taipei49314/greenwash/blob/main/benchmarks/corpus-expansion.md) | Is "once in 1800" a property of test-tampering or of six libraries that rarely stub anything? |
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
# 1. Clone wave 0 (small) so greenwash bench can see the published pins.
python -m corpus fetch --wave wave0-published-fp

# 2. Measure whether the clone has the power the rule needs.
python -m corpus census --wave wave0-published-fp

# 3. Harvest real merged PRs that touch tests (GitHub API, no clone required).
python -m corpus harvest-prs --wave wave0-published-fp --per-repo 15

# 4. Wave 1 is large. Depth 400, tens of GB, a round of its own.
python -m corpus fetch --wave wave1-mock-power
python -m corpus census --wave wave1-mock-power

# 5. Sweep — needs a greenwash/checkwash install on PATH.
python -m corpus sweep --wave wave0-published-fp --engine /path/to/greenwash
```

Point the engine at this cache:

```bash
export GREENWASH_CORPUS=/path/to/checkwash-corpus/clones
greenwash bench --corpus "$GREENWASH_CORPUS"
```

Or clone this repository as a sibling named `greenwash-corpus` and put the
wave-0 checkouts at that root (the layout `greenwash bench` already looks for).
`python -m corpus fetch --wave wave0-published-fp --layout bench` does that
when the repo itself is checked out as `greenwash-corpus`.

## What we will not do

- Vendor apache/airflow or huggingface/transformers into git.
- Publish a wave-1 false-positive rate before a census of that wave.
- Mix wave 0 and wave 1 in one headline number.
- Treat a harvested PR patch as a checkwash verdict. The engine has to say it.

## Layout

```
catalog/CATALOG.json     inclusion list (frozen probes, waves, pins)
records/sweeps/          greenwash sweep JSON, one file per source
records/census/          power counts at a named revision
records/prs/<id>/        harvested test-file patches from GitHub
records/incoming/        agent-diff drop-box
adjudication/            human FP/spec-correct split, after a sweep
clones/                  gitignored cache
src/corpus/              stdlib CLI
```

License: Apache-2.0 (this repository's tools and records). Third-party
projects keep their own licenses; we do not re-ship their trees.
