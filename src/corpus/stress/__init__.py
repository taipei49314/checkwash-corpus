"""corpus stress — 24-hour mechanical falsification of checkwash's own claims.

checkwash is a deterministic, sub-second static differ, so "stress" is not
load. It is four claims the project publishes and this package tries to break
for a day: recall (verified tampering must block), precision (verified honest
edits must pass), zero engine errors, and byte-identical verdicts.

Nothing here labels a mutant by hand. A tampering candidate counts only when
pytest goes red → green on buggy production with production byte-identical —
the tamper corpus's own definition. An honest candidate counts only when both
sides still catch the bug on buggy production and pass on correct production —
the refactor corpus's definition. Escapes and false positives are then verdicts
the engine gave on verified inputs, and every recorded finding is re-run
through the release zipapp on a real git repository before it is counted.

Two generation modes are reported separately: `rules` draws from an operator
library written against THREATMODEL's taxonomy (regression fuzzing — what a
spelling table would have caught); `open` applies random AST edits filtered by
the same oracles (discovery fuzzing — what the taxonomy does not name). A third
mode, `robust`, needs no oracle: malformed and pathological inputs must not
crash, must be deterministic, and must stay inside the perf budget.
"""
