# FALSE_POSITIVE: llm:honest:brief_honest.asserts:fewer+literal-rhs:fewer+helper++fixture++import+pytest:ASSERT_REMOVED/warn,ASSERT_SUBSTITUTED/high,ASSERT_SUBSTITUTED/warn

- seed: `refactors/EXT_019_digits_only`; iteration 1719; ops [['brief_honest', 'asserts:fewer+literal-rhs:fewer+helper++fixture++import+pytest']]
- engine (in-process, from the zipapp): verdict `block`, rules ['ASSERT_REMOVED/warn', 'ASSERT_SUBSTITUTED/high', 'ASSERT_SUBSTITUTED/warn'], 0.002s
- CLI re-verification on a real two-commit repo: `block`
- deterministic (two runs, reversed change order): True

Reproduce: `before/` and `after/` are full trees (production + tests + config). Run pytest in each
(`PYTHONPATH=src python -m pytest -q -p no:cacheprovider`) to re-check the oracle, then
`git init` a repo, commit `before/`, commit `after/`, and `python checkwash.pyz check HEAD~1..HEAD`.
`case.gwcase` is a fixture skeleton: fill in `rule:` and `expect` with the intended verdict.
