"""Seed triples: production (correct and buggy) plus a test suite that catches
the bug. Every generated mutant is a variation of a seed, and the seed's own
preconditions are checked with pytest before any mutant is trusted.

Sources, all from a checkwash checkout — this repository never vendors them:

    benchmarks/refactors/cases/*/PROD-GOOD, PROD-BUG, BEFORE   (both oracles)
    benchmarks/tamper/cases/*/src, before                     (tamper oracle only)

Each seed also carries a padding file of two trivial tests. An ordinary suite
has other tests, and pytest exits 5 (no tests ran — red in CI) when the only
test is neutralised; without padding, "delete the test" would never verify as
a wash, which is not how real suites behave. The padding is identical on both
sides, so it never enters the diff.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PADDING_PATH = "tests/test_zz_padding.py"
PADDING = '''"""Padding tests: an ordinary suite has other tests."""


def test_padding_arithmetic():
    assert 2 + 2 == 4


def test_padding_strings():
    assert "a".upper() == "A"
'''

BASELINE_INI = "[pytest]\ntestpaths = tests\n"


@dataclass
class Seed:
    id: str
    origin: str  # "refactors" | "tamper"
    prod_bug: dict[str, bytes]
    prod_good: dict[str, bytes] | None
    tests: dict[str, str]
    main_test: str
    modules: set[str]
    extras: dict[str, str] = field(default_factory=lambda: {"pytest.ini": BASELINE_INI})
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def honest_capable(self) -> bool:
        return self.prod_good is not None

    def main_source(self) -> str:
        return self.tests[self.main_test]


def _rel(p: Path, base: Path) -> str:
    return str(p.relative_to(base)).replace("\\", "/")


def _prod(src_dir: Path) -> dict[str, bytes]:
    return {f"src/{_rel(p, src_dir)}": p.read_bytes() for p in sorted(src_dir.rglob("*.py"))}


def _tests(tests_dir: Path) -> dict[str, str]:
    out = {}
    for p in sorted(tests_dir.rglob("*.py")):
        out[f"tests/{_rel(p, tests_dir)}"] = p.read_text(encoding="utf-8")
    return out


def _modules(prod: dict[str, bytes]) -> set[str]:
    mods: set[str] = set()
    for path in prod:
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == "src":
            mods.add(parts[1][:-3] if parts[1].endswith(".py") else parts[1])
    return mods


def _main_test(tests: dict[str, str]) -> str | None:
    for path in sorted(tests):
        name = path.rsplit("/", 1)[-1]
        if name.startswith("test_") and path != PADDING_PATH:
            return path
    return None


def load_seeds(checkwash_root: Path) -> list[Seed]:
    seeds: list[Seed] = []
    refactors = checkwash_root / "benchmarks" / "refactors" / "cases"
    if refactors.is_dir():
        for case in sorted(refactors.iterdir()):
            good, bug, before = case / "PROD-GOOD" / "src", case / "PROD-BUG" / "src", case / "BEFORE" / "tests"
            if not (good.is_dir() and bug.is_dir() and before.is_dir()):
                continue
            tests = _tests(before)
            main = _main_test(tests)
            if main is None:
                continue
            tests[PADDING_PATH] = PADDING
            prod_bug = _prod(bug)
            seeds.append(
                Seed(
                    id=f"refactors/{case.name}",
                    origin="refactors",
                    prod_bug=prod_bug,
                    prod_good=_prod(good),
                    tests=tests,
                    main_test=main,
                    modules=_modules(prod_bug),
                )
            )
    tamper = checkwash_root / "benchmarks" / "tamper" / "cases"
    if tamper.is_dir():
        for case in sorted(tamper.iterdir()):
            src, before = case / "src", case / "before" / "tests"
            if not (src.is_dir() and before.is_dir()):
                continue
            tests = _tests(before)
            main = _main_test(tests)
            if main is None:
                continue
            tests[PADDING_PATH] = PADDING
            prod_bug = _prod(src)
            seeds.append(
                Seed(
                    id=f"tamper/{case.name}",
                    origin="tamper",
                    prod_bug=prod_bug,
                    prod_good=None,
                    tests=tests,
                    main_test=main,
                    modules=_modules(prod_bug),
                )
            )
    return seeds
