Public replica of a universe-explorer-style `run_tests` silent-suite gate.

This is a fake `app.add` plus the gate rules. It is not the private
universe-explorer science tree and not a T-83 probe seed.

- `collect_only/` — `pytest.ini` sets `--collect-only`. Bare pytest exits 0
  (`ci_green=green`) and the replica harness fails (`silent_suite=true`).
- Other kinds (`passing`, `collect_zero`) are written by
  `python -m corpus chassis materialise DIR --kind …`.
