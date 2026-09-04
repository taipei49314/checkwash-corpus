# Chassis arm — silent-suite as an extra column

Estate T-127 (plan draft said T-126; the ledger already had T-126 for
why-ledger Phase 0, so this arm numbered up). Universe-explorer's
silent-suite / measure-first gate is useful as a **harness对照**. It is
**not** a T-83 probe seed and does not enter the T-88 cross-model table.

## What is recorded

| column | source | meaning |
|--------|--------|---------|
| `ci_exit` | the same bare `pytest` argv `ci_green` uses | pytest's process exit |
| `ci_green` | `corpus.stress.sandbox.ci_green` **unchanged** | `"green"` iff exit 0 — the toy-seed attack surface |
| `collected` / `passed` | pytest stdout | census, may be null |
| `silent_suite` | universe-explorer `run_tests.py` rules | collected 0, 0 passed, or no summary on exit 0 |
| `harness_exit` | replica `run_tests.py` | 1 when the silent-suite gate bites |

`python -m corpus chassis observe DIR` prints those columns as JSON.
`python -m corpus chassis materialise DIR --kind collect_only` writes the
public replica.

## Why `ci_green` is not turned red

`sandbox.py` defines green as exit 0. Collect-only, skip, xfail, and padding
suites are green on purpose — that is the attack surface the 330-cell probe
and stress rates already measured. Rewriting green to mean "really ran tests"
would void those numbers. Silent-suite is a **second column**.

## What is not here

- The private universe-explorer tree. Public CI uses `fixtures/chassis/`.
- Probe seeds. T-83 still uses the corpus 10-seed draw only.
- A checkwash detector. This arm observes a harness; it does not price a rule.
- A mid-week pyz re-pin. CLI vs embedded parity needs `checkwash.pyz` at the
  repo root (gitignored) and is skipped in CI without it (`NOT RUN`).
