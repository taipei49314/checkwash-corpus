# tools

`watch_engine.py` polls `taipei49314/checkwash` every two minutes.

- New **Release** `checkwash.pyz` → `DONE release <tag> <sha256>` → ledger sweep with the zipapp.
- New **main commit** → `DONE commit <sha> …` → smoke only, not `records/sweeps/`.

Baseline is whatever HEAD/tag exists when the watcher first starts, so the current tree is not re-measured on launch.

`post_hanging_records.py` copies engine JSON/MD into `records/field-runs/`
and splits the already-written wave0 adjudication file. It does not invent
counts. Zipapps stay gitignored (`*.pyz`).

