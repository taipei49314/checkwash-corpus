# tools/llm-arm

`rejudge_llm_cli.py` re-judges a recorded stress record (`records/stress/<run>/`,
one directory per ESCAPE / FALSE_POSITIVE family with full `before/` and `after/`
trees) through the zipapp's **CLI path only**: each family becomes a fresh
two-commit git repository, materialised with the same helpers
`corpus.stress.engine.blackbox_check` uses, and `python checkwash.pyz check
HEAD~1..HEAD --format json` is run in it. The in-process judge is not used
(it lacks the strict-snapshot wiring checkwash's own adapters use since 0.3.0,
issue #15).

```bash
python tools/llm-arm/rejudge_llm_cli.py \
    --record records/stress/llm-2026-09-03 \
    --pyz /path/to/checkwash.pyz \
    --out /path/to/out \
    --limit 0            # 0 = every family; N = the first N of each class (trial)
```

Outputs: `results.json` (meta, per-family rows, summary), `SUMMARY.md`
(recorded-CLI → now-CLI verdict matrix per class, highest-severity histogram,
flips, errors) and `cli/<class>/<family>.json` (raw CLI output). Exit code 1
when any family errored or timed out.

The record's own `outcome.json` per family carries the in-process verdict and
the CLI verdict at record time (`blackbox`); the summary compares against the
recorded CLI verdict, and each row also states whether the new verdict differs
from the recorded in-process one.
