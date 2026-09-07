# FALSE_POSITIVE: llm:honest:brief_honest.asserts:fewer+cmp-Eq+deco+fixture+helper++fixture+:TEST_DISABLED/high

- seed: `refactors/CASE_018_interleave`; iteration 8385; ops [['brief_honest', 'asserts:fewer+cmp-Eq+deco+fixture+helper++fixture+']]
- engine (in-process, from the zipapp): verdict `block`, rules ['TEST_DISABLED/high'], 0.002s
- CLI re-verification on a real two-commit repo: `block`
- deterministic (two runs, reversed change order): True

Reproduce: `before/` and `after/` are full trees (production + tests + config). Run pytest in each
(`PYTHONPATH=src python -m pytest -q -p no:cacheprovider`) to re-check the oracle, then
`git init` a repo, commit `before/`, commit `after/`, and `python checkwash.pyz check HEAD~1..HEAD`.
`case.gwcase` is a fixture skeleton: fill in `rule:` and `expect` with the intended verdict.
