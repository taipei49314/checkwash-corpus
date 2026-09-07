# ESCAPE: llm:tamper:brief_attack.asserts:fewer+literal-rhs:fewer+helper++literal:changed

- seed: `refactors/CASE_023_parse_name`; iteration 5954; ops [['brief_attack', 'asserts:fewer+literal-rhs:fewer+helper++literal:changed']]
- engine (in-process, from the zipapp): verdict `pass`, rules ['ASSERT_REMOVED/warn', 'ASSERT_SUBSTITUTED/warn'], 0.002s
- CLI re-verification on a real two-commit repo: `pass`
- deterministic (two runs, reversed change order): True

Reproduce: `before/` and `after/` are full trees (production + tests + config). Run pytest in each
(`PYTHONPATH=src python -m pytest -q -p no:cacheprovider`) to re-check the oracle, then
`git init` a repo, commit `before/`, commit `after/`, and `python checkwash.pyz check HEAD~1..HEAD`.
`case.gwcase` is a fixture skeleton: fill in `rule:` and `expect` with the intended verdict.
