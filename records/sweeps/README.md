# Sweep records

One JSON file per catalog id, written by `python -m corpus sweep`.

The payload is the engine's own sweep JSON plus `catalog_id`, `wave`, and
`engine` (`asset` + `sha256`). Published wave-1 files must be run with
`checkwash.pyz` (or `greenwash.pyz` on tags ≤v0.1.49). The 2026-09-01
wave-0 reproduction is grandfathered as `editable-unrecorded`.

`python -m corpus validate` refuses a file that is missing corpus pins,
engine version, or a publishable `engine` record. A wave-1 sweep without
a matching census is invalid.

Do not hand-edit numbers. Re-run the sweep.
