# Collaboration protocol (humans and coding agents)

## Engine pin follows the checkwash release slot (estate T-57 D-4, 2026-09-03)

- Sweeps and stress runs use a Release `checkwash.pyz`, fetched once after each
  checkwash release slot (weekly; the slot is defined in the estate PLAN). Do
  not fetch or re-pin between slots.
- `--allow-stale-engine` exists to measure an old version on purpose. It is not
  a way around a missing re-pin: if the guard in `src/corpus/stress/run.py`
  refuses, the slot's re-pin has not happened yet. Wait for it, or do it in
  that slot's PR.
- Frozen: `wave2-js-oracle` is not scheduled. Nothing is fetched or measured
  for it until a human opens that round.
- Public repository: open a PR, do not merge it. The human merges.
