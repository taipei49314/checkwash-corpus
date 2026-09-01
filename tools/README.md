# tools

`watch_engine.py` polls `taipei49314/checkwash` every two minutes.

- New **Release** `checkwash.pyz` → `DONE release <tag> <sha256>` → ledger sweep with the zipapp.
- New **main commit** → `DONE commit <sha> …` → smoke only, not `records/sweeps/`.

Baseline is whatever HEAD/tag exists when the watcher first starts, so the current tree is not re-measured on launch.
