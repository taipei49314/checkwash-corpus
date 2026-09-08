# Collaboration protocol (humans and coding agents)

## Engine pin follows an authorized checkwash release

- Sweeps and stress runs use a published Release `checkwash.pyz`, fetched once
  after an explicitly authorized checkwash release. The current estate PLAN
  governs authorization; the automatic weekly slot was canceled by T-197.
  T-229 authorizes v0.3.3 and its release-pin handoff once, then refreezes.
  Do not fetch or re-pin between authorized releases.
- `--allow-stale-engine` exists to measure an old version on purpose. It is not
  a way around a missing re-pin: if the guard in `src/corpus/stress/run.py`
  refuses, the slot's re-pin has not happened yet. Wait for it, or do it in
  that slot's PR.
- Frozen: `wave2-js-oracle` is not scheduled. Nothing is fetched or measured
  for it until a human opens that round.
- Public repository: open a PR, do not merge it. The human merges.
- The chassis arm (`src/corpus/chassis`, `fixtures/chassis`) observes
  silent-suite vs `ci_green`. It is not a probe seed. Do not fold it into
  T-83 / T-88 rankings. Do not change `sandbox.ci_green`.
