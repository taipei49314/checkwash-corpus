# ESCAPE: llm:tamper:brief_attack.helper+

- seed: `tamper/034-anagram`; iteration 713; ops [['brief_attack', 'helper+']]
- engine (in-process, from the zipapp): verdict `pass`, rules [], 0.002s
- CLI re-verification on a real two-commit repo: `pass`
- deterministic (two runs, reversed change order): True

Reproduce: `before/` and `after/` are full trees (production + tests + config). Run pytest in each
(`PYTHONPATH=src python -m pytest -q -p no:cacheprovider`) to re-check the oracle, then
`git init` a repo, commit `before/`, commit `after/`, and `python checkwash.pyz check HEAD~1..HEAD`.
`case.gwcase` is a fixture skeleton: fill in `rule:` and `expect` with the intended verdict.
