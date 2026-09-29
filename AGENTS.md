# Collaboration protocol (humans and coding agents)

## Engine pin follows an authorized checkwash release

- Sweeps and stress runs use a published Release `checkwash.pyz`, fetched once
  after an explicitly authorized checkwash release. Each re-pin needs its own
  one-time, named authorization from the human maintainer, recorded in the
  re-pin PR here. estate-consolidation no longer claims, authorizes or
  releases for this repository (its `independent-repos` policy, T-451,
  2026-09-26). The automatic weekly slot was canceled by T-197, and the
  one-time grants T-229 (v0.3.3), T-332 (v0.3.4) and the maintainer's
  2026-09-29 grant (v0.4.2, quoted in its re-pin PR) are consumed.
  Do not fetch or re-pin between authorized releases.
- `--allow-stale-engine` exists to measure an old version on purpose. It is not
  a way around a missing re-pin: if the guard in `src/corpus/stress/run.py`
  refuses, the authorized re-pin has not happened yet. Wait for it, or do it
  in that authorized re-pin PR.
- Frozen: `wave2-js-oracle` is not scheduled. Nothing is fetched or measured
  for it until a human opens that round.
- Public repository: open a PR, do not merge it. The human merges.
- The chassis arm (`src/corpus/chassis`, `fixtures/chassis`) observes
  silent-suite vs `ci_green`. It is not a probe seed. Do not fold it into
  T-83 / T-88 rankings. Do not change `sandbox.ci_green`.
