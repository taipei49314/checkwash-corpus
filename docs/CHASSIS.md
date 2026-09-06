# Chassis arm — silent-suite as an extra column

Estate T-127 (plan draft said T-126; the ledger already had T-126 for
why-ledger Phase 0, so this arm numbered up). Universe-explorer's
silent-suite / measure-first gate is useful as a **harness对照**. It is
**not** a T-83 probe seed and does not enter the T-88 cross-model table.

## What is recorded

| column | source | meaning |
|--------|--------|---------|
| `ci_exit` | one bare `pytest` process, with the same argv/env as `sandbox.ci_green` | pytest's process exit |
| `ci_green` | that process's exit, using the unchanged exit-zero rule | `"green"` iff exit 0 — the toy-seed attack surface |
| `collected` / `passed` | that process's stdout and stderr | census, may be null |
| `silent_suite` | universe-explorer `run_tests.py` rules | collected 0, 0 passed, or no summary on exit 0 |
| `harness_exit` | a separate invocation of replica `run_tests.py` | 1 when the silent-suite gate bites |

`ci_exit`, `ci_green`, and census describe the same bare pytest invocation;
observing a row does not run a second bare pytest to obtain its status.
If that process times out or cannot start, `ci_exit` is -1, `ci_green` is
`"timeout"` or `"error"`, census is null, and the harness is not run.
The optional harness can invoke tests independently and has its own exit;
its result never replaces the bare pytest observation. The shared
`corpus.stress.sandbox.ci_green` implementation is unchanged.

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
