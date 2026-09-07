# checkwash stress run — llm-2026-09-03

Engine: `checkwash.pyz` v0.2.8 (sha256 `83878db57a243386…`). 12929 iterations in 5.25 h, 4 workers, PRNG seed `2026-09-03`, modes llm. Seeds: 140/140 usable.

## Calibration (must pass before any number below is believed)

- ok `refactor_ledger`: blocks=24, expected_blocks=24
- ok `tamper_ledger`: blocks=49, expected_blocks=49
- ok `oracle_plumbing`: cases=80
- ok `sensitivity`: recorded_escapes=31, classified_as_escape=31
- overall: **PASS**

## Headline

Finding families: ESCAPE 88, FALSE_POSITIVE 90.
A family is one hole (operator chain + spelling, plus the rules that fired for false positives); the count is how many verified mutants fell through it. Every family's first instance was re-run through the zipapp CLI on a real two-commit repository (`CLI re-check`); a divergence from the in-process verdict is itself a finding.

## By mode

| mode | generated | verified | ESCAPE | FALSE_POSITIVE | CRASH | NONDET | DISCARDED | INAPPLICABLE | NOOP | OK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| llm | 12929 | 2262 | 477 | 268 | 0 | 0 | 10224 | 0 | 65 | 1517 |

`verified` = the mechanical oracle agreed (tamper/open: red→green on buggy production; honest: still red on buggy, green on correct). `DISCARDED` = the edit did not verify and was thrown away, not counted against the engine.

## Rule-space arm (operators written against THREATMODEL's taxonomy)

### Escapes — verified tampering the engine passed

_none_

### False positives — verified honest refactors the engine blocked

_none_

## Open-ended arm (random AST edits, oracle-filtered)

### Escapes

_none_

## Robustness

### Crashes / bad verdicts

_none_

### Non-determinism (same input, reversed change order, different output)

_none_

### Perf

Inputs over budget while measured under load: 0. Re-measured alone (median of three) after the workers drained: none still over budget.

## LLM arm (a local model proposes, the oracle decides)

Model `qwen2.5-coder:7b` at `http://127.0.0.1:11434`, temperature 0.9. Nothing the model says is evidence: every proposal went through the same parse gate, unsafe-source scan, pytest oracle and pinned engine as the operator arms. Family keys are AST shape signatures of the edit; the model's own TACTIC line is stored in `proposal.json` next to each repro for the human who triages.

| brief | generated | verified | ESCAPE | FALSE_POSITIVE |
|---|---:|---:|---:|---:|
| attack | 9219 | 1041 | 432 | 0 |
| config | 2294 | 543 | 45 | 0 |
| honest | 1416 | 678 | 0 | 268 |

Discarded before or at the oracle: oracle_discarded 10187, NOOP 65, SYNTAX 20, NO_FENCE 13, EMPTY 2, WRONG_TARGET 2.

Model server errors (backed off, not counted as findings): 378.

### Escapes — verified tampering the engine passed

| family | count | CLI re-check | repro |
|---|---:|---|---|
| `llm:tamper:brief_attack.literal-rhs:fewer+call+approx+import+pytest+literal:changed` | 41 | pass | `escapes/004-llm-tamper-brief_attack.literal-rhs-fewer-call-approx-import-pytest-literal-chan` |
| `llm:tamper:brief_attack.literal-rhs:fewer+deco+mark.parametrize+call+mark.parametrize+import+pytest+literal:changed` | 41 | pass | `escapes/005-llm-tamper-brief_attack.literal-rhs-fewer-deco-mark.parametrize-call-mark.parame` |
| `llm:tamper:brief_attack.literal-rhs:fewer+helper++fixture++import+pytest+literal:changed` | 39 | pass | `escapes/022-llm-tamper-brief_attack.literal-rhs-fewer-helper-fixture-import-pytest-literal-c` |
| `llm:tamper:brief_attack.literal-rhs:fewer+helper++literal:changed` | 33 | pass | `escapes/006-llm-tamper-brief_attack.literal-rhs-fewer-helper-literal-changed` |
| `llm:tamper:brief_config.ini:addopts,testpaths` | 29 | pass | `escapes/007-llm-tamper-brief_config.ini-addopts-testpaths` |
| `llm:tamper:brief_attack.literal:changed` | 22 | pass | `escapes/011-llm-tamper-brief_attack.literal-changed` |
| `llm:tamper:brief_attack.tests:fewer+asserts:fewer+deco+mark.parametrize+call+mark.parametrize+import+pytest` | 17 | pass | `escapes/001-llm-tamper-brief_attack.tests-fewer-asserts-fewer-deco-mark.parametrize-call-mar` |
| `llm:tamper:brief_attack.helper+` | 16 | pass | `escapes/008-llm-tamper-brief_attack.helper` |
| `llm:tamper:brief_config.ini:addopts` | 16 | pass | `escapes/023-llm-tamper-brief_config.ini-addopts` |
| `llm:tamper:brief_attack.tests:fewer+asserts:fewer+literal-rhs:fewer+deco+mark.parametrize+call+mark.parametrize` | 15 | pass | `escapes/002-llm-tamper-brief_attack.tests-fewer-asserts-fewer-literal-rhs-fewer-deco-mark.pa` |
| `llm:tamper:brief_attack.helper++literal:changed` | 14 | pass | `escapes/030-llm-tamper-brief_attack.helper-literal-changed` |
| `llm:tamper:brief_attack.literal-rhs:fewer+deco+mark.parametrize+call+approx+call+mark.parametrize+import+pytest` | 14 | pass | `escapes/003-llm-tamper-brief_attack.literal-rhs-fewer-deco-mark.parametrize-call-approx-call` |
| `llm:tamper:brief_attack.literal-rhs:fewer+literal:changed` | 12 | pass | `escapes/025-llm-tamper-brief_attack.literal-rhs-fewer-literal-changed` |
| `llm:tamper:brief_attack.asserts:fewer+literal-rhs:fewer+deco+mark.parametrize+call+mark.parametrize+import+pytest` | 11 | pass | `escapes/010-llm-tamper-brief_attack.asserts-fewer-literal-rhs-fewer-deco-mark.parametrize-ca` |
| `llm:tamper:brief_attack.text-only` | 10 | pass | `escapes/040-llm-tamper-brief_attack.text-only` |
| `llm:tamper:brief_attack.deco+mark.parametrize+call+mark.parametrize+import+pytest+literal:changed` | 9 | pass | `escapes/032-llm-tamper-brief_attack.deco-mark.parametrize-call-mark.parametrize-import-pytes` |
| `llm:tamper:brief_attack.helper++fixture++import+pytest+literal:changed` | 8 | pass | `escapes/021-llm-tamper-brief_attack.helper-fixture-import-pytest-literal-changed` |
| `llm:tamper:brief_attack.tests:fewer+asserts:fewer+cmp-Is+literal-rhs:fewer+deco+mark.parametrize` | 8 | pass | `escapes/063-llm-tamper-brief_attack.tests-fewer-asserts-fewer-cmp-Is-literal-rhs-fewer-deco` |
| `llm:tamper:brief_attack.asserts:fewer+cmp+Eq+deco+mark.parametrize+call+mark.parametrize+import+pytest` | 7 | pass | `escapes/020-llm-tamper-brief_attack.asserts-fewer-cmp-Eq-deco-mark.parametrize-call-mark.par` |
| `llm:tamper:brief_attack.cmp+Eq+cmp-Is+literal-rhs:fewer+helper++literal:changed` | 7 | pass | `escapes/045-llm-tamper-brief_attack.cmp-Eq-cmp-Is-literal-rhs-fewer-helper-literal-changed` |
| `llm:tamper:brief_attack.tests:fewer+deco+mark.parametrize+call+mark.parametrize+import+pytest+literal:changed` | 7 | pass | `escapes/038-llm-tamper-brief_attack.tests-fewer-deco-mark.parametrize-call-mark.parametrize` |
| `llm:tamper:brief_attack.helper++fixture++import+pytest` | 6 | pass | `escapes/034-llm-tamper-brief_attack.helper-fixture-import-pytest` |
| `llm:tamper:brief_attack.tests:fewer+asserts:more+cmp+Eq+deco+mark.parametrize+call+mark.parametrize` | 6 | pass | `escapes/018-llm-tamper-brief_attack.tests-fewer-asserts-more-cmp-Eq-deco-mark.parametrize-ca` |
| `llm:tamper:brief_attack.cmp+Is+literal-rhs:more+literal:changed` | 5 | pass | `escapes/016-llm-tamper-brief_attack.cmp-Is-literal-rhs-more-literal-changed` |
| `llm:tamper:brief_attack.tests:fewer+asserts:fewer+deco+mark.parametrize+call+approx+call+mark.parametrize` | 4 | pass | `escapes/027-llm-tamper-brief_attack.tests-fewer-asserts-fewer-deco-mark.parametrize-call-app` |
| `llm:tamper:brief_attack.asserts:fewer+cmp+Is+cmp-Eq+literal-rhs:fewer+deco+mark.parametrize` | 3 | pass | `escapes/058-llm-tamper-brief_attack.asserts-fewer-cmp-Is-cmp-Eq-literal-rhs-fewer-deco-mark.` |
| `llm:tamper:brief_attack.call+approx+import+pytest+literal:changed` | 3 | pass | `escapes/019-llm-tamper-brief_attack.call-approx-import-pytest-literal-changed` |
| `llm:tamper:brief_attack.asserts:fewer+cmp+Eq+literal-rhs:more+literal:changed` | 2 | pass | `escapes/014-llm-tamper-brief_attack.asserts-fewer-cmp-Eq-literal-rhs-more-literal-changed` |
| `llm:tamper:brief_attack.asserts:fewer+deco+mark.parametrize+helper++call+mark.parametrize+import+pytest` | 2 | pass | `escapes/064-llm-tamper-brief_attack.asserts-fewer-deco-mark.parametrize-helper-call-mark.par` |
| `llm:tamper:brief_attack.asserts:fewer+literal-rhs:fewer+helper++literal:changed` | 2 | pass | `escapes/061-llm-tamper-brief_attack.asserts-fewer-literal-rhs-fewer-helper-literal-changed` |
| `llm:tamper:brief_attack.cmp+Eq+deco+mark.parametrize+helper++fixture++call+mark.parametrize` | 2 | pass | `escapes/036-llm-tamper-brief_attack.cmp-Eq-deco-mark.parametrize-helper-fixture-call-mark.pa` |
| `llm:tamper:brief_attack.cmp+Eq+helper++fixture++import+pytest+literal:changed` | 2 | pass | `escapes/043-llm-tamper-brief_attack.cmp-Eq-helper-fixture-import-pytest-literal-changed` |
| `llm:tamper:brief_attack.cmp+Eq+literal-rhs:more+helper+` | 2 | pass | `escapes/051-llm-tamper-brief_attack.cmp-Eq-literal-rhs-more-helper` |
| `llm:tamper:brief_attack.literal-rhs:fewer+deco+mark.parametrize+ctl+For+call+mark.parametrize+import+pytest` | 2 | pass | `escapes/054-llm-tamper-brief_attack.literal-rhs-fewer-deco-mark.parametrize-ctl-For-call-mar` |
| `llm:tamper:brief_attack.literal-rhs:fewer+deco+mark.parametrize+helper++call+mark.parametrize+import+pytest` | 2 | pass | `escapes/033-llm-tamper-brief_attack.literal-rhs-fewer-deco-mark.parametrize-helper-call-mark` |
| `llm:tamper:brief_attack.literal-rhs:fewer+deco+mark.parametrize+helper++fixture++call+mark.parametrize` | 2 | pass | `escapes/026-llm-tamper-brief_attack.literal-rhs-fewer-deco-mark.parametrize-helper-fixture-c` |
| `llm:tamper:brief_attack.tests:fewer+asserts:fewer+cmp+Eq+cmp-Is+literal-rhs:fewer` | 2 | pass | `escapes/069-llm-tamper-brief_attack.tests-fewer-asserts-fewer-cmp-Eq-cmp-Is-literal-rhs-fewe` |
| `llm:tamper:brief_attack.tests:fewer+asserts:fewer+literal-rhs:fewer+deco+mark.parametrize+helper+` | 2 | pass | `escapes/062-llm-tamper-brief_attack.tests-fewer-asserts-fewer-literal-rhs-fewer-deco-mark.pa` |
| `llm:tamper:brief_attack.tests:fewer+asserts:more+cmp+Is+deco+mark.parametrize+call+mark.parametrize` | 2 | pass | `escapes/024-llm-tamper-brief_attack.tests-fewer-asserts-more-cmp-Is-deco-mark.parametrize-ca` |
| `llm:tamper:brief_attack.with+patch+import+unittest+literal:changed` | 2 | pass | `escapes/009-llm-tamper-brief_attack.with-patch-import-unittest-literal-changed` |
| `llm:tamper:brief_attack.asserts:fewer+cmp+Eq+deco+mark.parametrize+call+approx+call+mark.parametrize` | 1 | pass | `escapes/012-llm-tamper-brief_attack.asserts-fewer-cmp-Eq-deco-mark.parametrize-call-approx-c` |
| `llm:tamper:brief_attack.asserts:fewer+cmp-Eq+literal-rhs:fewer+helper++import+pytest` | 1 | pass | `escapes/044-llm-tamper-brief_attack.asserts-fewer-cmp-Eq-literal-rhs-fewer-helper-import-pyt` |
| `llm:tamper:brief_attack.asserts:fewer+cmp-Eq+literal-rhs:fewer+with+raises+helper+` | 1 | pass | `escapes/065-llm-tamper-brief_attack.asserts-fewer-cmp-Eq-literal-rhs-fewer-with-raises-helpe` |
| `llm:tamper:brief_attack.asserts:fewer+cmp-In+literal-rhs:fewer+literal:changed` | 1 | pass | `escapes/048-llm-tamper-brief_attack.asserts-fewer-cmp-In-literal-rhs-fewer-literal-changed` |
| `llm:tamper:brief_attack.asserts:fewer+helper++literal:changed` | 1 | pass | `escapes/068-llm-tamper-brief_attack.asserts-fewer-helper-literal-changed` |
| `llm:tamper:brief_attack.asserts:fewer+literal-rhs:fewer+ctl+For` | 1 | pass | `escapes/053-llm-tamper-brief_attack.asserts-fewer-literal-rhs-fewer-ctl-For` |
| `llm:tamper:brief_attack.asserts:fewer+literal-rhs:fewer+helper++fixture++ctl+For` | 1 | pass | `escapes/083-llm-tamper-brief_attack.asserts-fewer-literal-rhs-fewer-helper-fixture-ctl-For` |
| `llm:tamper:brief_attack.asserts:more+cmp+Eq+deco+mark.parametrize+call+approx+call+mark.parametrize` | 1 | pass | `escapes/073-llm-tamper-brief_attack.asserts-more-cmp-Eq-deco-mark.parametrize-call-approx-ca` |
| `llm:tamper:brief_attack.asserts:more+cmp+Eq+helper++ctl+For+literal:changed` | 1 | pass | `escapes/074-llm-tamper-brief_attack.asserts-more-cmp-Eq-helper-ctl-For-literal-changed` |
| `llm:tamper:brief_attack.asserts:more+cmp+Eq+literal-rhs:more+deco+patch+import+unittest` | 1 | pass | `escapes/047-llm-tamper-brief_attack.asserts-more-cmp-Eq-literal-rhs-more-deco-patch-import-u` |
| `llm:tamper:brief_attack.asserts:more+cmp+Eq+with+patch+import+unittest+literal:changed` | 1 | pass | `escapes/085-llm-tamper-brief_attack.asserts-more-cmp-Eq-with-patch-import-unittest-literal-c` |
| `llm:tamper:brief_attack.asserts:more+cmp+Is+literal-rhs:more+literal:changed` | 1 | pass | `escapes/017-llm-tamper-brief_attack.asserts-more-cmp-Is-literal-rhs-more-literal-changed` |
| `llm:tamper:brief_attack.asserts:more+helper++literal:changed` | 1 | pass | `escapes/050-llm-tamper-brief_attack.asserts-more-helper-literal-changed` |
| `llm:tamper:brief_attack.asserts:more+literal-rhs:more+helper++fixture++import+pytest` | 1 | pass | `escapes/075-llm-tamper-brief_attack.asserts-more-literal-rhs-more-helper-fixture-import-pyte` |
| `llm:tamper:brief_attack.cmp+Eq+cmp-Is+literal-rhs:fewer+helper++fixture+` | 1 | pass | `escapes/057-llm-tamper-brief_attack.cmp-Eq-cmp-Is-literal-rhs-fewer-helper-fixture` |
| `llm:tamper:brief_attack.cmp+Eq+deco+mark.parametrize+call+mark.parametrize+import+pytest+literal:changed` | 1 | pass | `escapes/072-llm-tamper-brief_attack.cmp-Eq-deco-mark.parametrize-call-mark.parametrize-impor` |
| `llm:tamper:brief_attack.cmp+Eq+helper++call+approx+import+pytest` | 1 | pass | `escapes/031-llm-tamper-brief_attack.cmp-Eq-helper-call-approx-import-pytest` |
| `llm:tamper:brief_attack.cmp+Eq+helper++fixture++ctl+For+import+pytest` | 1 | pass | `escapes/013-llm-tamper-brief_attack.cmp-Eq-helper-fixture-ctl-For-import-pytest` |
| `llm:tamper:brief_attack.cmp+Is+cmp-Eq+literal-rhs:fewer+helper++fixture+` | 1 | pass | `escapes/055-llm-tamper-brief_attack.cmp-Is-cmp-Eq-literal-rhs-fewer-helper-fixture` |
| `llm:tamper:brief_attack.cmp-Is+literal-rhs:fewer+deco+fixture+fixture++ctl+For` | 1 | pass | `escapes/046-llm-tamper-brief_attack.cmp-Is-literal-rhs-fewer-deco-fixture-fixture-ctl-For` |
| `llm:tamper:brief_attack.ctl+Return+literal:changed` | 1 | pass | `escapes/039-llm-tamper-brief_attack.ctl-Return-literal-changed` |
| `llm:tamper:brief_attack.deco+mark.parametrize+helper++call+mark.parametrize+import+pytest+literal:changed` | 1 | pass | `escapes/035-llm-tamper-brief_attack.deco-mark.parametrize-helper-call-mark.parametrize-impor` |
| `llm:tamper:brief_attack.helper++import+math` | 1 | pass | `escapes/081-llm-tamper-brief_attack.helper-import-math` |
| `llm:tamper:brief_attack.import+pytest+literal:changed` | 1 | pass | `escapes/052-llm-tamper-brief_attack.import-pytest-literal-changed` |
| `llm:tamper:brief_attack.literal-rhs:fewer+deco+mark.parametrize+ctl+Try+call+mark.parametrize+import+pytest` | 1 | pass | `escapes/077-llm-tamper-brief_attack.literal-rhs-fewer-deco-mark.parametrize-ctl-Try-call-mar` |
| `llm:tamper:brief_attack.literal-rhs:fewer+deco+mark.parametrize+fixture++call+mark.parametrize+import+pytest` | 1 | pass | `escapes/084-llm-tamper-brief_attack.literal-rhs-fewer-deco-mark.parametrize-fixture-call-mar` |
| `llm:tamper:brief_attack.literal-rhs:fewer+helper+` | 1 | pass | `escapes/088-llm-tamper-brief_attack.literal-rhs-fewer-helper` |
| `llm:tamper:brief_attack.literal-rhs:fewer+helper++ctl+For+literal:changed` | 1 | pass | `escapes/082-llm-tamper-brief_attack.literal-rhs-fewer-helper-ctl-For-literal-changed` |
| `llm:tamper:brief_attack.literal-rhs:fewer+helper++fixture++call+approx+import+pytest` | 1 | pass | `escapes/015-llm-tamper-brief_attack.literal-rhs-fewer-helper-fixture-call-approx-import-pyte` |
| `llm:tamper:brief_attack.literal-rhs:fewer+helper++fixture++literal:changed` | 1 | pass | `escapes/079-llm-tamper-brief_attack.literal-rhs-fewer-helper-fixture-literal-changed` |
| `llm:tamper:brief_attack.literal-rhs:fewer+helper++import+pytest+literal:changed` | 1 | pass | `escapes/041-llm-tamper-brief_attack.literal-rhs-fewer-helper-import-pytest-literal-changed` |
| `llm:tamper:brief_attack.tests:fewer+asserts:fewer+cmp-Eq+cmp-In+literal-rhs:fewer` | 1 | pass | `escapes/028-llm-tamper-brief_attack.tests-fewer-asserts-fewer-cmp-Eq-cmp-In-literal-rhs-fewe` |
| `llm:tamper:brief_attack.tests:fewer+cmp+Eq+literal-rhs:more+helper++fixture+` | 1 | pass | `escapes/071-llm-tamper-brief_attack.tests-fewer-cmp-Eq-literal-rhs-more-helper-fixture` |
| `llm:tamper:brief_attack.tests:fewer+deco+patch+import+unittest+import+unittest+literal:changed` | 1 | pass | `escapes/037-llm-tamper-brief_attack.tests-fewer-deco-patch-import-unittest-import-unittest-l` |
| `llm:tamper:brief_attack.tests:more+asserts:more+cmp+Eq+cmp+Is+literal-rhs:more` | 1 | pass | `escapes/029-llm-tamper-brief_attack.tests-more-asserts-more-cmp-Eq-cmp-Is-literal-rhs-more` |
| `llm:tamper:brief_attack.tests:more+asserts:more+cmp+Eq+deco+fixture+fixture+` | 1 | pass | `escapes/086-llm-tamper-brief_attack.tests-more-asserts-more-cmp-Eq-deco-fixture-fixture` |
| `llm:tamper:brief_attack.tests:more+asserts:more+literal-rhs:fewer+helper++literal:changed` | 1 | pass | `escapes/076-llm-tamper-brief_attack.tests-more-asserts-more-literal-rhs-fewer-helper-literal` |
| `llm:tamper:brief_attack.tests:more+asserts:more+literal-rhs:more+helper++literal:changed` | 1 | pass | `escapes/080-llm-tamper-brief_attack.tests-more-asserts-more-literal-rhs-more-helper-literal` |
| `llm:tamper:brief_attack.tests:more+asserts:more+literal-rhs:more+with+raises+call+raises` | 1 | pass | `escapes/056-llm-tamper-brief_attack.tests-more-asserts-more-literal-rhs-more-with-raises-cal` |
| `llm:tamper:brief_attack.tests:more+asserts:more+literal-rhs:more+with+raises+helper+` | 1 | pass | `escapes/060-llm-tamper-brief_attack.tests-more-asserts-more-literal-rhs-more-with-raises-hel` |
| `llm:tamper:brief_attack.tests:more+cmp+Eq+deco+fixture+deco+mark.parametrize+fixture+` | 1 | pass | `escapes/087-llm-tamper-brief_attack.tests-more-cmp-Eq-deco-fixture-deco-mark.parametrize-fix` |
| `llm:tamper:brief_attack.tests:more+literal-rhs:fewer+ctl+For+literal:changed` | 1 | pass | `escapes/049-llm-tamper-brief_attack.tests-more-literal-rhs-fewer-ctl-For-literal-changed` |
| `llm:tamper:brief_attack.tests:more+literal-rhs:fewer+deco+fixture+fixture++ctl+Return` | 1 | pass | `escapes/059-llm-tamper-brief_attack.tests-more-literal-rhs-fewer-deco-fixture-fixture-ctl-Re` |
| `llm:tamper:brief_attack.tests:more+literal-rhs:fewer+deco+fixture+helper++fixture+` | 1 | pass | `escapes/070-llm-tamper-brief_attack.tests-more-literal-rhs-fewer-deco-fixture-helper-fixture` |
| `llm:tamper:brief_attack.tests:more+literal-rhs:fewer+deco+mark.parametrize+helper++fixture+` | 1 | pass | `escapes/067-llm-tamper-brief_attack.tests-more-literal-rhs-fewer-deco-mark.parametrize-helpe` |
| `llm:tamper:brief_attack.tests:more+literal-rhs:fewer+with+raises+deco+mark.parametrize+helper+` | 1 | pass | `escapes/042-llm-tamper-brief_attack.tests-more-literal-rhs-fewer-with-raises-deco-mark.param` |
| `llm:tamper:brief_attack.tests:more+literal-rhs:fewer+with+raises+helper++call+raises` | 1 | pass | `escapes/078-llm-tamper-brief_attack.tests-more-literal-rhs-fewer-with-raises-helper-call-rai` |
| `llm:tamper:brief_attack.with+patch.object+import+unittest+literal:changed` | 1 | pass | `escapes/066-llm-tamper-brief_attack.with-patch.object-import-unittest-literal-changed` |

### False positives — verified honest refactors the engine blocked

| family | count | CLI re-check | repro |
|---|---:|---|---|
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+helper++fixture+:TEST_DISABLED/high` | 36 | block | `false_positives/004-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-helper-fixtu` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+deco+fixture+fixture+:TEST_DISABLED/high` | 25 | block | `false_positives/025-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-deco-fixture` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+deco+fixture+fixture++ctl+Return:TEST_DISABLED/high` | 17 | block | `false_positives/002-llm-honest-brief_honest.tests-fewer-asserts-fewer-deco-fixture-fixture-ctl-Retur` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+ctl+For:TEST_DISABLED/high` | 15 | block | `false_positives/005-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-ctl-For-TEST` |
| `llm:honest:brief_honest.tests:more+literal-rhs:fewer+deco+fixture+fixture++ctl+Return:ASSERT_SUBSTITUTED/high` | 12 | block | `false_positives/012-llm-honest-brief_honest.tests-more-literal-rhs-fewer-deco-fixture-fixture-ctl-Re` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+cmp+Eq+cmp-Is+literal-rhs:fewer:TEST_DISABLED/high` | 8 | block | `false_positives/014-llm-honest-brief_honest.tests-fewer-asserts-fewer-cmp-Eq-cmp-Is-literal-rhs-fewe` |
| `llm:honest:brief_honest.tests:more+deco+fixture+fixture++ctl+Return+import+pytest:ASSERT_WEAKENED/high` | 7 | block | `false_positives/036-llm-honest-brief_honest.tests-more-deco-fixture-fixture-ctl-Return-import-pytest` |
| `llm:honest:brief_honest.asserts:fewer+literal-rhs:fewer+deco+fixture+fixture++ctl+Return:TEST_DISABLED/high` | 6 | block | `false_positives/006-llm-honest-brief_honest.asserts-fewer-literal-rhs-fewer-deco-fixture-fixture-ctl` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+helper++fixture++import+pytest:TEST_DISABLED/high` | 6 | block | `false_positives/003-llm-honest-brief_honest.tests-fewer-asserts-fewer-helper-fixture-import-pytest-T` |
| `llm:honest:brief_honest.asserts:fewer+deco+fixture+fixture++ctl+Return+import+pytest:TEST_DISABLED/high` | 5 | block | `false_positives/001-llm-honest-brief_honest.asserts-fewer-deco-fixture-fixture-ctl-Return-import-pyt` |
| `llm:honest:brief_honest.helper+:SUBJECT_NORMALIZED/high` | 5 | block | `false_positives/015-llm-honest-brief_honest.helper-SUBJECT_NORMALIZED-high` |
| `llm:honest:brief_honest.literal-rhs:fewer+helper++fixture++import+pytest+literal:changed:ASSERT_SUBSTITUTED/high` | 5 | block | `false_positives/032-llm-honest-brief_honest.literal-rhs-fewer-helper-fixture-import-pytest-literal-c` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+ctl+For+literal:changed:TEST_DISABLED/high` | 5 | block | `false_positives/017-llm-honest-brief_honest.tests-fewer-asserts-fewer-ctl-For-literal-changed-TEST_D` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+ctl+For+literal:changed:TEST_DISABLED/high` | 5 | block | `false_positives/008-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-ctl-For-lite` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+helper++ctl+For:TEST_DISABLED/high` | 5 | block | `false_positives/016-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-helper-ctl-F` |
| `llm:honest:brief_honest.tests:more+deco+fixture+fixture++ctl+Return+import+pytest:ASSERT_REMOVED/high` | 5 | block | `false_positives/057-llm-honest-brief_honest.tests-more-deco-fixture-fixture-ctl-Return-import-pytest` |
| `llm:honest:brief_honest.tests:more+literal-rhs:fewer+deco+fixture+fixture++ctl+For:ASSERT_SUBSTITUTED/high` | 5 | block | `false_positives/050-llm-honest-brief_honest.tests-more-literal-rhs-fewer-deco-fixture-fixture-ctl-Fo` |
| `llm:honest:brief_honest.tests:more+asserts:fewer+cmp-Eq+deco+fixture+helper+:ASSERT_WEAKENED/high` | 4 | block | `false_positives/022-llm-honest-brief_honest.tests-more-asserts-fewer-cmp-Eq-deco-fixture-helper-ASSE` |
| `llm:honest:brief_honest.asserts:fewer+helper++fixture++import+pytest+literal:changed:ASSERT_REMOVED/warn,ASSERT_WEAKENED/high` | 3 | block | `false_positives/037-llm-honest-brief_honest.asserts-fewer-helper-fixture-import-pytest-literal-chang` |
| `llm:honest:brief_honest.helper++fixture++import+pytest+literal:changed:ASSERT_WEAKENED/high` | 3 | block | `false_positives/033-llm-honest-brief_honest.helper-fixture-import-pytest-literal-changed-ASSERT_WEAK` |
| `llm:honest:brief_honest.asserts:fewer+cmp-Eq+helper+:ASSERT_WEAKENED/high` | 2 | block | `false_positives/074-llm-honest-brief_honest.asserts-fewer-cmp-Eq-helper-ASSERT_WEAKENED-high` |
| `llm:honest:brief_honest.asserts:fewer+ctl+For+literal:changed:ASSERT_REMOVED/warn,ASSERT_WEAKENED/high` | 2 | block | `false_positives/054-llm-honest-brief_honest.asserts-fewer-ctl-For-literal-changed-ASSERT_REMOVED-war` |
| `llm:honest:brief_honest.asserts:fewer+literal-rhs:fewer+deco+fixture+fixture++ctl+For:TEST_DISABLED/high` | 2 | block | `false_positives/031-llm-honest-brief_honest.asserts-fewer-literal-rhs-fewer-deco-fixture-fixture-ctl` |
| `llm:honest:brief_honest.asserts:fewer+literal-rhs:fewer+helper++fixture++import+pytest:ASSERT_REMOVED/warn,ASSERT_SUBSTITUTED/high,ASSERT_SUBSTITUTED/warn` | 2 | block | `false_positives/023-llm-honest-brief_honest.asserts-fewer-literal-rhs-fewer-helper-fixture-import-py` |
| `llm:honest:brief_honest.helper++fixture++ctl+For+import+pytest+literal:changed:ASSERT_WEAKENED/high` | 2 | block | `false_positives/048-llm-honest-brief_honest.helper-fixture-ctl-For-import-pytest-literal-changed-ASS` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+cmp+Eq+cmp-Is+literal-rhs:fewer:ASSERT_SUBSTITUTED/high,TEST_DISABLED/high` | 2 | block | `false_positives/018-llm-honest-brief_honest.tests-fewer-asserts-fewer-cmp-Eq-cmp-Is-literal-rhs-fewe` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+cmp-Eq+literal-rhs:fewer+helper+:TEST_DISABLED/high` | 2 | block | `false_positives/021-llm-honest-brief_honest.tests-fewer-asserts-fewer-cmp-Eq-literal-rhs-fewer-helpe` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+cmp-In+cmp-NotIn+literal-rhs:fewer:TEST_DISABLED/high` | 2 | block | `false_positives/063-llm-honest-brief_honest.tests-fewer-asserts-fewer-cmp-In-cmp-NotIn-literal-rhs-f` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+deco+mark.parametrize+call+mark.parametrize:TEST_DISABLED/high` | 2 | block | `false_positives/058-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-deco-mark.pa` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+deco+mark.parametrize+helper+:TEST_DISABLED/high` | 2 | block | `false_positives/083-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-deco-mark.pa` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+helper++fixture+:ASSERT_SUBSTITUTED/high,TEST_DISABLED/high` | 2 | block | `false_positives/081-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-helper-fixtu` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+helper++fixture+:TEST_DISABLED/high,TEST_DISABLED/warn` | 2 | block | `false_positives/026-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-helper-fixtu` |
| `llm:honest:brief_honest.tests:more+asserts:more+literal-rhs:more+literal:changed:ASSERT_REMOVED/high` | 2 | block | `false_positives/051-llm-honest-brief_honest.tests-more-asserts-more-literal-rhs-more-literal-changed` |
| `llm:honest:brief_honest.tests:more+cmp-Is+literal-rhs:fewer+deco+fixture+fixture+:ASSERT_SUBSTITUTED/high` | 2 | block | `false_positives/047-llm-honest-brief_honest.tests-more-cmp-Is-literal-rhs-fewer-deco-fixture-fixture` |
| `llm:honest:brief_honest.tests:more+literal-rhs:fewer+deco+fixture+helper++fixture+:ASSERT_SUBSTITUTED/high` | 2 | block | `false_positives/056-llm-honest-brief_honest.tests-more-literal-rhs-fewer-deco-fixture-helper-fixture` |
| `llm:honest:brief_honest.text-only:ASSERT_SUBSTITUTED/high,EXPECTED_VALUE_CHANGED/high` | 2 | block | `false_positives/040-llm-honest-brief_honest.text-only-ASSERT_SUBSTITUTED-high-EXPECTED_VALUE_CHANGED` |
| `llm:honest:brief_honest.asserts:fewer+cmp+Eq+cmp-Is+literal-rhs:fewer+deco+fixture:ASSERT_SUBSTITUTED/high,TEST_DISABLED/high` | 1 | block | `false_positives/077-llm-honest-brief_honest.asserts-fewer-cmp-Eq-cmp-Is-literal-rhs-fewer-deco-fixtu` |
| `llm:honest:brief_honest.asserts:fewer+cmp-Eq+cmp-In+cmp-NotIn+literal-rhs:fewer:EXPECTED_VALUE_DERIVED/high` | 1 | block | `false_positives/084-llm-honest-brief_honest.asserts-fewer-cmp-Eq-cmp-In-cmp-NotIn-literal-rhs-fewer` |
| `llm:honest:brief_honest.asserts:fewer+cmp-Eq+deco+fixture+helper++fixture+:TEST_DISABLED/high` | 1 | block | `false_positives/072-llm-honest-brief_honest.asserts-fewer-cmp-Eq-deco-fixture-helper-fixture-TEST_DI` |
| `llm:honest:brief_honest.asserts:fewer+cmp-Eq+deco+mark.parametrize+helper++call+mark.parametrize:ASSERT_REMOVED/high` | 1 | block | `false_positives/046-llm-honest-brief_honest.asserts-fewer-cmp-Eq-deco-mark.parametrize-helper-call-m` |
| `llm:honest:brief_honest.asserts:fewer+cmp-Eq+helper++fixture++import+pytest:ASSERT_WEAKENED/high` | 1 | block | `false_positives/071-llm-honest-brief_honest.asserts-fewer-cmp-Eq-helper-fixture-import-pytest-ASSERT` |
| `llm:honest:brief_honest.asserts:fewer+cmp-Eq+literal-rhs:fewer+helper++literal:changed:ASSERT_REMOVED/high` | 1 | block | `false_positives/049-llm-honest-brief_honest.asserts-fewer-cmp-Eq-literal-rhs-fewer-helper-literal-ch` |
| `llm:honest:brief_honest.asserts:fewer+cmp-In+cmp-NotIn+helper++fixture+:ASSERT_REMOVED/high` | 1 | block | `false_positives/010-llm-honest-brief_honest.asserts-fewer-cmp-In-cmp-NotIn-helper-fixture-ASSERT_REM` |
| `llm:honest:brief_honest.asserts:fewer+cmp-In+cmp-NotIn+helper++literal:changed:ASSERT_WEAKENED/high,EXPECTED_VALUE_CHANGED/high` | 1 | block | `false_positives/052-llm-honest-brief_honest.asserts-fewer-cmp-In-cmp-NotIn-helper-literal-changed-AS` |
| `llm:honest:brief_honest.asserts:fewer+ctl+For:ASSERT_REMOVED/warn,ASSERT_WEAKENED/high` | 1 | block | `false_positives/068-llm-honest-brief_honest.asserts-fewer-ctl-For-ASSERT_REMOVED-warn-ASSERT_WEAKENE` |
| `llm:honest:brief_honest.asserts:fewer+deco+fixture+fixture++ctl+For+ctl+Return:TEST_DISABLED/high` | 1 | block | `false_positives/073-llm-honest-brief_honest.asserts-fewer-deco-fixture-fixture-ctl-For-ctl-Return-TE` |
| `llm:honest:brief_honest.asserts:fewer+helper++fixture++ctl+For+import+pytest:ASSERT_REMOVED/warn,ASSERT_WEAKENED/high` | 1 | block | `false_positives/041-llm-honest-brief_honest.asserts-fewer-helper-fixture-ctl-For-import-pytest-ASSER` |
| `llm:honest:brief_honest.asserts:fewer+literal-rhs:fewer+deco+fixture+helper++fixture+:TEST_DISABLED/high` | 1 | block | `false_positives/064-llm-honest-brief_honest.asserts-fewer-literal-rhs-fewer-deco-fixture-helper-fixt` |
| `llm:honest:brief_honest.asserts:fewer+literal-rhs:fewer+deco+mark.parametrize+ctl+For+ctl+Return:TEST_DISABLED/high` | 1 | block | `false_positives/060-llm-honest-brief_honest.asserts-fewer-literal-rhs-fewer-deco-mark.parametrize-ct` |
| `llm:honest:brief_honest.asserts:fewer+literal-rhs:fewer+literal:changed:ASSERT_REMOVED/high` | 1 | block | `false_positives/061-llm-honest-brief_honest.asserts-fewer-literal-rhs-fewer-literal-changed-ASSERT_R` |
| `llm:honest:brief_honest.asserts:fewer+literal-rhs:fewer+with+raises+helper++fixture+:TEST_DISABLED/high` | 1 | block | `false_positives/062-llm-honest-brief_honest.asserts-fewer-literal-rhs-fewer-with-raises-helper-fixtu` |
| `llm:honest:brief_honest.asserts:more+helper+:ASSERT_WEAKENED/high` | 1 | block | `false_positives/088-llm-honest-brief_honest.asserts-more-helper-ASSERT_WEAKENED-high` |
| `llm:honest:brief_honest.cmp+Eq+cmp-Is+literal-rhs:fewer+deco+mark.parametrize+ctl+For:TEST_DISABLED/high` | 1 | block | `false_positives/044-llm-honest-brief_honest.cmp-Eq-cmp-Is-literal-rhs-fewer-deco-mark.parametrize-ct` |
| `llm:honest:brief_honest.cmp-Eq+literal-rhs:fewer+helper++literal:changed:ASSERT_WEAKENED/high` | 1 | block | `false_positives/079-llm-honest-brief_honest.cmp-Eq-literal-rhs-fewer-helper-literal-changed-ASSERT_W` |
| `llm:honest:brief_honest.ctl+For+literal:changed:ASSERT_REMOVED/high` | 1 | block | `false_positives/027-llm-honest-brief_honest.ctl-For-literal-changed-ASSERT_REMOVED-high` |
| `llm:honest:brief_honest.deco+fixture+fixture++ctl+Return+import+pytest+literal:changed:TEST_DISABLED/high,TEST_DISABLED/info` | 1 | block | `false_positives/029-llm-honest-brief_honest.deco-fixture-fixture-ctl-Return-import-pytest-literal-ch` |
| `llm:honest:brief_honest.deco+mark.parametrize+call+mark.parametrize+import+pytest+literal:changed:ASSERT_REMOVED/high` | 1 | block | `false_positives/070-llm-honest-brief_honest.deco-mark.parametrize-call-mark.parametrize-import-pytes` |
| `llm:honest:brief_honest.helper++fixture++import+pytest+literal:changed:ASSERT_SUBSTITUTED/high,EXPECTED_VALUE_CHANGED/high` | 1 | block | `false_positives/028-llm-honest-brief_honest.helper-fixture-import-pytest-literal-changed-ASSERT_SUBS` |
| `llm:honest:brief_honest.helper++fixture++literal:changed:TEST_DISABLED/high` | 1 | block | `false_positives/090-llm-honest-brief_honest.helper-fixture-literal-changed-TEST_DISABLED-high` |
| `llm:honest:brief_honest.literal-rhs:fewer+ctl+For+literal:changed:TEST_DISABLED/high` | 1 | block | `false_positives/019-llm-honest-brief_honest.literal-rhs-fewer-ctl-For-literal-changed-TEST_DISABLED` |
| `llm:honest:brief_honest.literal-rhs:fewer+deco+mark.parametrize+call+mark.parametrize+literal:changed:ASSERT_SUBSTITUTED/high` | 1 | block | `false_positives/087-llm-honest-brief_honest.literal-rhs-fewer-deco-mark.parametrize-call-mark.parame` |
| `llm:honest:brief_honest.literal-rhs:fewer+helper++fixture++ctl+For+ctl+If:ASSERT_SUBSTITUTED/high` | 1 | block | `false_positives/030-llm-honest-brief_honest.literal-rhs-fewer-helper-fixture-ctl-For-ctl-If-ASSERT_S` |
| `llm:honest:brief_honest.literal-rhs:fewer+helper++fixture++ctl+For+import+pytest:ASSERT_SUBSTITUTED/high` | 1 | block | `false_positives/045-llm-honest-brief_honest.literal-rhs-fewer-helper-fixture-ctl-For-import-pytest-A` |
| `llm:honest:brief_honest.literal-rhs:fewer+helper++fixture++literal:changed:TEST_DISABLED/high` | 1 | block | `false_positives/086-llm-honest-brief_honest.literal-rhs-fewer-helper-fixture-literal-changed-TEST_DI` |
| `llm:honest:brief_honest.literal-rhs:fewer+literal:changed:ASSERT_WEAKENED/high` | 1 | block | `false_positives/055-llm-honest-brief_honest.literal-rhs-fewer-literal-changed-ASSERT_WEAKENED-high` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+cmp-Eq+literal-rhs:fewer+with+self.subTest:TEST_DISABLED/high` | 1 | block | `false_positives/076-llm-honest-brief_honest.tests-fewer-asserts-fewer-cmp-Eq-literal-rhs-fewer-with` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+cmp-Eq+literal-rhs:fewer+with+self.subTest:TEST_DISABLED/high,TEST_DISABLED/warn` | 1 | block | `false_positives/085-llm-honest-brief_honest.tests-fewer-asserts-fewer-cmp-Eq-literal-rhs-fewer-with` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+cmp-Is+literal-rhs:fewer+helper+:ASSERT_SUBSTITUTED/high,TEST_DISABLED/high` | 1 | block | `false_positives/080-llm-honest-brief_honest.tests-fewer-asserts-fewer-cmp-Is-literal-rhs-fewer-helpe` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+deco+fixture+fixture++ctl+For:TEST_DISABLED/high` | 1 | block | `false_positives/039-llm-honest-brief_honest.tests-fewer-asserts-fewer-deco-fixture-fixture-ctl-For-T` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+deco+fixture+helper++fixture+:TEST_DISABLED/high` | 1 | block | `false_positives/009-llm-honest-brief_honest.tests-fewer-asserts-fewer-deco-fixture-helper-fixture-TE` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+ctl+For+literal:changed:ASSERT_SUBSTITUTED/high,EXPECTED_VALUE_CHANGED/high,TEST_DISABLED/high` | 1 | block | `false_positives/075-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-ctl-For-lite` |
| `llm:honest:brief_honest.tests:fewer+asserts:fewer+literal-rhs:fewer+deco+fixture+helper+:TEST_DISABLED/high` | 1 | block | `false_positives/082-llm-honest-brief_honest.tests-fewer-asserts-fewer-literal-rhs-fewer-deco-fixture` |
| `llm:honest:brief_honest.tests:fewer+asserts:more+cmp+Eq+deco+fixture+fixture+:TEST_DISABLED/high,TEST_DISABLED/info` | 1 | block | `false_positives/069-llm-honest-brief_honest.tests-fewer-asserts-more-cmp-Eq-deco-fixture-fixture-TES` |
| `llm:honest:brief_honest.tests:fewer+asserts:more+cmp+Eq+deco+mark.parametrize+call+mark.parametrize:TEST_DISABLED/high` | 1 | block | `false_positives/038-llm-honest-brief_honest.tests-fewer-asserts-more-cmp-Eq-deco-mark.parametrize-ca` |
| `llm:honest:brief_honest.tests:fewer+asserts:more+cmp+Eq+deco+mark.parametrize+call+mark.parametrize:TEST_DISABLED/high,TEST_DISABLED/info` | 1 | block | `false_positives/089-llm-honest-brief_honest.tests-fewer-asserts-more-cmp-Eq-deco-mark.parametrize-ca` |
| `llm:honest:brief_honest.tests:fewer+asserts:more+cmp+Eq+fixture++import+pytest:TEST_DISABLED/high,TEST_DISABLED/info` | 1 | block | `false_positives/043-llm-honest-brief_honest.tests-fewer-asserts-more-cmp-Eq-fixture-import-pytest-TE` |
| `llm:honest:brief_honest.tests:fewer+asserts:more+cmp+Eq+literal-rhs:more+with+raises:TEST_DISABLED/high,TEST_DISABLED/info` | 1 | block | `false_positives/067-llm-honest-brief_honest.tests-fewer-asserts-more-cmp-Eq-literal-rhs-more-with-ra` |
| `llm:honest:brief_honest.tests:fewer+asserts:more+cmp+Is+deco+fixture+fixture+:TEST_DISABLED/high,TEST_DISABLED/info` | 1 | block | `false_positives/035-llm-honest-brief_honest.tests-fewer-asserts-more-cmp-Is-deco-fixture-fixture-TES` |
| `llm:honest:brief_honest.tests:fewer+ctl+For:TEST_DISABLED/high,TEST_DISABLED/info` | 1 | block | `false_positives/011-llm-honest-brief_honest.tests-fewer-ctl-For-TEST_DISABLED-high-TEST_DISABLED-inf` |
| `llm:honest:brief_honest.tests:fewer+deco+mark.parametrize+helper++call+mark.parametrize+import+pytest:TEST_DISABLED/high` | 1 | block | `false_positives/007-llm-honest-brief_honest.tests-fewer-deco-mark.parametrize-helper-call-mark.param` |
| `llm:honest:brief_honest.tests:fewer+helper++fixture++import+pytest+literal:changed:TEST_DISABLED/high` | 1 | block | `false_positives/034-llm-honest-brief_honest.tests-fewer-helper-fixture-import-pytest-literal-changed` |
| `llm:honest:brief_honest.tests:fewer+with+self.subTest+ctl+For+literal:changed:TEST_DISABLED/high` | 1 | block | `false_positives/042-llm-honest-brief_honest.tests-fewer-with-self.subTest-ctl-For-literal-changed-TE` |
| `llm:honest:brief_honest.tests:fewer+with+self.subTest+helper++ctl+For+literal:changed:TEST_DISABLED/high` | 1 | block | `false_positives/013-llm-honest-brief_honest.tests-fewer-with-self.subTest-helper-ctl-For-literal-cha` |
| `llm:honest:brief_honest.tests:more+asserts:fewer+cmp-Eq+deco+fixture+helper+:ASSERT_REMOVED/high` | 1 | block | `false_positives/024-llm-honest-brief_honest.tests-more-asserts-fewer-cmp-Eq-deco-fixture-helper-ASSE` |
| `llm:honest:brief_honest.tests:more+asserts:fewer+cmp-Eq+helper++ctl+Return:ASSERT_WEAKENED/high` | 1 | block | `false_positives/059-llm-honest-brief_honest.tests-more-asserts-fewer-cmp-Eq-helper-ctl-Return-ASSERT` |
| `llm:honest:brief_honest.tests:more+asserts:fewer+literal-rhs:fewer+deco+fixture+fixture+:ASSERT_REMOVED/warn,ASSERT_SUBSTITUTED/high,ASSERT_SUBSTITUTED/warn` | 1 | block | `false_positives/053-llm-honest-brief_honest.tests-more-asserts-fewer-literal-rhs-fewer-deco-fixture` |
| `llm:honest:brief_honest.tests:more+asserts:more+literal-rhs:more+ctl+For+literal:changed:ASSERT_SUBSTITUTED/high,EXPECTED_VALUE_CHANGED/high` | 1 | block | `false_positives/020-llm-honest-brief_honest.tests-more-asserts-more-literal-rhs-more-ctl-For-literal` |
| `llm:honest:brief_honest.tests:more+deco+fixture+fixture++ctl+For+ctl+Return:ASSERT_WEAKENED/high` | 1 | block | `false_positives/078-llm-honest-brief_honest.tests-more-deco-fixture-fixture-ctl-For-ctl-Return-ASSER` |
| `llm:honest:brief_honest.tests:more+literal-rhs:fewer+deco+fixture+fixture++ctl+Return:TEST_DISABLED/high` | 1 | block | `false_positives/065-llm-honest-brief_honest.tests-more-literal-rhs-fewer-deco-fixture-fixture-ctl-Re` |
| `llm:honest:brief_honest.text-only:ASSERT_SUBSTITUTED/high` | 1 | block | `false_positives/066-llm-honest-brief_honest.text-only-ASSERT_SUBSTITUTED-high` |

## Coverage — rule-space tamper operators

_none_

## Coverage — rule-space honest operators

_none_

## Coverage — open-ended edits

_none_

## Coverage — robustness inputs

_none_

## Limits, stated

- Only pytest-runnable configuration is generated (pytest.ini, conftest.py). CI workflow and Makefile weakenings have no mechanical oracle in this harness and are not measured here.
- Seeds are the three shipped corpora: small single-function production. Larger shapes (fixtures, classes, cross-file helpers) are under-represented.
- Every seed carries a two-test padding file so a neutralised test does not empty the run; that is the realistic suite shape, and it is identical on both sides.
- `async_convert` (an orphan `async def` test with no async plugin) is pytest-version-dependent: some versions skip it (green — a wash), others fail it. The oracle decides per run; a verified escape here means *this* pytest skipped it.
- Open-ended edits explore only the palette in `random_ops.py`; a family the palette cannot express is not in this report.
- The LLM arm (`--modes llm`) is the escape hatch for shapes the palette cannot express: a local model proposes whole-file rewrites of the seed's test file (or a pytest.ini), and the same oracle and engine decide. Nothing the model says is evidence; its findings are candidates like every other family, and its TACTIC labels are never family keys.
- Findings are candidates: `case.gwcase` skeletons carry `rule: TODO` and are not committed by the harness (AGENTS.md rule 2 — labels are reviewed by a human).
