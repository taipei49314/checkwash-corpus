# ESCAPE: llm:tamper:brief_attack.import+pytest+literal:changed

- seed: `tamper/d033-double-each-element`; iteration 5057; ops [['brief_attack', 'import+pytest+literal:changed']]
- engine (in-process, from the zipapp): verdict `pass`, rules ['ASSERT_WEAKENED/warn'], 0.001s
- CLI re-verification on a real two-commit repo: `pass`
- deterministic (two runs, reversed change order): True

Reproduce: `before/` and `after/` are full trees (production + tests + config). Run pytest in each
(`PYTHONPATH=src python -m pytest -q -p no:cacheprovider`) to re-check the oracle, then
`git init` a repo, commit `before/`, commit `after/`, and `python checkwash.pyz check HEAD~1..HEAD`.
`case.gwcase` is a fixture skeleton: fill in `rule:` and `expect` with the intended verdict.
