# Record shapes

Frozen by `python -m corpus validate` and SPEC §4. JSON, sorted keys, UTF-8.

Sweep records wrap greenwash's sweep payload and add `catalog_id` + `wave`.
Field-run records are copied into `records/field-runs/<date>/` with the same
engine pin/sha256 gate; they are not catalog rows. Census records copy
`probes` from the catalog so a later probe edit cannot rewrite history.
Harvest identity is `(owner_repo, pr_number, head_sha)`.
