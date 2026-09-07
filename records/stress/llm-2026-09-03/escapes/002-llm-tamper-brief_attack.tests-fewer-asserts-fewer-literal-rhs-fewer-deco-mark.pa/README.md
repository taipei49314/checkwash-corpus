# ESCAPE: llm:tamper:brief_attack.tests:fewer+asserts:fewer+literal-rhs:fewer+deco+mark.parametrize+call+mark.parametrize

- seed: `refactors/EXT_001_indent`; iteration 39; ops [['brief_attack', 'tests:fewer+asserts:fewer+literal-rhs:fewer+deco+mark.parametrize+call+mark.parametrize']]
- engine (in-process, from the zipapp): verdict `pass`, rules ['TEST_DISABLED/warn'], 0.002s
- CLI re-verification on a real two-commit repo: `pass`
- deterministic (two runs, reversed change order): True

Reproduce: `before/` and `after/` are full trees (production + tests + config). Run pytest in each
(`PYTHONPATH=src python -m pytest -q -p no:cacheprovider`) to re-check the oracle, then
`git init` a repo, commit `before/`, commit `after/`, and `python checkwash.pyz check HEAD~1..HEAD`.
`case.gwcase` is a fixture skeleton: fill in `rule:` and `expect` with the intended verdict.
