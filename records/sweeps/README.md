# Sweep records

One JSON file per catalog id, written by `python -m corpus sweep`.

The payload is greenwash's own sweep JSON plus `catalog_id` and `wave`.
`python -m corpus validate` refuses a file that is missing
`corpus.newest_commit`, `corpus.oldest_commit`, and the engine version.

Do not hand-edit numbers. Re-run the sweep.
