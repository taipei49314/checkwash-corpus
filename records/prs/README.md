# Harvested pull requests

Merged GitHub PRs whose changed files include a test path from the catalog
(or a `test_*.py` / `*_test.py` / `*.test.*` / `*.spec.*` fallback).

Written by `python -m corpus harvest-prs`. Identity is
`(owner_repo, pr_number, head_sha)` — a second harvest of the same identity
is a no-op.

Each file stores test-file patches only, capped. This is not a checkwash
verdict and not a substitute for `greenwash check` on the real range.
