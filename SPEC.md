# checkwash-corpus SPEC

This file is the contract for what counts as a measurement. Coding agents
may add sources, records, and tools; they may not silently skip a missing
clone, mix waves in a published aggregate, or vendor a third-party tree.

Schema version: 1

## 1. What this repository is

A **ledger and harvest pipeline** for real-world checkwash
measurements. It is not the engine. It does not judge diffs. Verdicts come
from a checkwash/greenwash checkout pointed at a clone this repo fetched.

greenwash already knows this shape: `greenwash bench --corpus DIR` (or
`GREENWASH_CORPUS`, or a sibling named `greenwash-corpus`) expects one git
clone per published sweep stem. Default fetch layout (`cache`) writes
`clones/<id>`. `--layout bench` writes wave-0 clones at the repo root
(`./flask`, `./httpx`, …) so a checkout named `greenwash-corpus` is the
directory bench already looks for. Wave 1 always stays under `clones/`.

## 2. Evidence vs cache

| path | in git? | role |
|------|---------|------|
| `catalog/CATALOG.json` | yes | inclusion list, waves, frozen power probes |
| `records/sweeps/*.json` | yes | recorded `greenwash sweep` output |
| `records/census/*.json` | yes | power measurement at a named revision |
| `records/prs/**` | yes | harvested GitHub PR test-file patches |
| `records/incoming/**` | yes | drop-box for agent diffs (see that README) |
| `adjudication/` | yes | human verdicts; empty until a sweep exists |
| `clones/` | **never** | local git cache of third-party trees |

A record without the pins in §4 is not a measurement. A clone without a
record is just disk.

## 3. Waves do not mix

Each published number names exactly one wave. Wave 0 is the six-repo
false-positive corpus greenwash already publishes; its job is reproducing
those numbers, not estimating mock-power. Wave 1 exists because wave 0
cannot see `TEST_PATCHES_SUBJECT` (THREATMODEL 90): ≈128 patch call sites
across six libraries vs 31,641 across the twenty expansion candidates.

Adding a source to a wave whose published aggregate already exists is a
new round, with its own red-zone reconciliation — not a silent extra row.

## 4. Required pins

Every sweep record must carry:

- `catalog_id`, `wave`
- `corpus.newest_commit`, `corpus.oldest_commit`
- `corpus.greenwash_version` (or `checkwash_version`)
- `commits_analysed`, `commits_blocked`, `engine_errors`
- `engine.asset` + `engine.sha256`:
  - current Release zipapp: `checkwash.pyz` and a 64-hex sha256
  - tags ≤v0.1.49: `greenwash.pyz` and a 64-hex sha256
  - the 2026-09-01 wave-0 reproduction only: `editable-unrecorded` / `sha256: null`
    (version string drifted; not a pin). New wave-1 records may not use this.

A PATH executable or editable checkout is a dirty engine. `sweep` refuses it
unless `--allow-dirty-engine`. Dirty records fail `validate` on wave 1.

Every census record must carry:

- `catalog_id`, `wave`, `revision`
- `probes` (the frozen regex set from the catalog, copied not implied)
- per-probe counts

New census writes also record `clone_depth` and `bytes_on_disk`. Older
census files without those keys stay valid.

A wave-1 sweep file with no matching `records/census/<id>.json` is invalid
(power before precision).

`python -m corpus validate` refuses a record that is missing any of these.
Missing is a hard fail, not a skipped row.

## 5. Fail closed

- Fetch of a catalogued, `include: true` source that cannot be cloned exits
  non-zero and names the source. It does not continue and print a partial
  table as if it were complete.
- A directory whose `.git` is incomplete, or whose `rev-parse --show-toplevel`
  is this corpus rather than itself, is **broken**, not cloned (`status`
  says `broken`; fetch/census/sweep refuse it).
- Sweep of a clone that does not contain the requested pin exits non-zero.
- Census of a missing clone exits non-zero for that source.
- `include: false` sources are invisible to fetch/census/sweep unless
  `--include-planned` is passed. Planned is not measured.

## 6. Third-party source is never vendored

Clones stay in `clones/`, gitignored. Harvested PR records store **test-file
patches only**, capped, with `owner/repo`, PR number, and head SHA so the
full diff can be re-fetched. That is excerpt-as-evidence, not a mirror.

Licenses in the catalog are the project's declared license at cataloguing
time. Redistributing a clone as part of this repository is out of scope.

## 7. Determinism of machine records

- JSON: sorted keys, `ensure_ascii=False`, `\n` line endings, UTF-8.
- Sweep and census records contain no wall-clock timestamps. Identity is
  `(catalog_id, revision)` for census and `(catalog_id, newest, oldest,
  engine)` for sweeps.
- Harvest records may carry `harvested_at` (ISO date). It is a collection
  event, not part of identity. Identity is `(owner_repo, pr_number, head_sha)`.
  A second harvest of the same identity is a no-op, not an overwrite.

## 8. Power before precision

A false-positive rate on a corpus that cannot see the rule is not a
false-positive rate (greenwash THREATMODEL 90). Census runs before any
wave-1 sweep is published. The probes are frozen in the catalog; changing
them is a schema bump.

## 9. Adjudication

A sweep JSON is a machine count. The false-positive split is a human
judgement and lives under `adjudication/`. Pairing a fresh sweep with a
stale adjudication is refused by `validate` the same way greenwash's
`make_results.py` refuses it: the blocked `(id, commit)` set must match
exactly.

## 10. Exit codes

`0` complete success;
`1` a catalogued unit failed (missing clone, pin, harvest, or validation);
`2` tool/input error (bad args, catalog unreadable, `gh`/`git` missing).
