# Sweep records

One JSON file per catalog id, written by `python -m corpus sweep`.

The payload is the engine's own sweep JSON plus `catalog_id`, `wave`, and
`engine` (`asset` + `sha256`). Published files must be run with
`checkwash.pyz` (or `greenwash.pyz` on tags ≤v0.1.49). Dirty engines and
the closed `editable-unrecorded` grandfather fail `validate`.

Field-run copies belong in `records/field-runs/`, not here. Do not mix
waves. Do not hand-edit numbers. Re-run the sweep.
