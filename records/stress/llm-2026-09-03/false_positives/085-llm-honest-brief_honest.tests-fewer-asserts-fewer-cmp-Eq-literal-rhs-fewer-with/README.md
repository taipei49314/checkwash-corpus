# FALSE_POSITIVE: llm:honest:brief_honest.tests:fewer+asserts:fewer+cmp-Eq+literal-rhs:fewer+with+self.subTest:TEST_DISABLED/high,TEST_DISABLED/warn

- seed: `refactors/CASE_016_digit_sum`; iteration 10882; ops [['brief_honest', 'tests:fewer+asserts:fewer+cmp-Eq+literal-rhs:fewer+with+self.subTest']]
- engine (in-process, from the zipapp): verdict `block`, rules ['TEST_DISABLED/high', 'TEST_DISABLED/warn'], 0.001s
- CLI re-verification on a real two-commit repo: `block`
- deterministic (two runs, reversed change order): True

Reproduce: `before/` and `after/` are full trees (production + tests + config). Run pytest in each
(`PYTHONPATH=src python -m pytest -q -p no:cacheprovider`) to re-check the oracle, then
`git init` a repo, commit `before/`, commit `after/`, and `python checkwash.pyz check HEAD~1..HEAD`.
`case.gwcase` is a fixture skeleton: fill in `rule:` and `expect` with the intended verdict.
