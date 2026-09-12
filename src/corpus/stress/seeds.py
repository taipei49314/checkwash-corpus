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

from corpus.stress.inventory import SeedInventoryError, fixture_cases, seed_tree

PADDING_PATH = "tests/test_zz_padding.py"
PADDING = '''"""Padding tests: an ordinary suite has other tests."""


def test_padding_arithmetic():
    assert 2 + 2 == 4


def test_padding_strings():
    assert "a".upper() == "A"
'''

BASELINE_INI = "[pytest]\ntestpaths = tests\n"
CONFIG_NAMES = {"pytest.ini", ".pytest.ini", "pytest.toml", ".pytest.toml", "tox.ini", "setup.cfg", "pyproject.toml"}


@dataclass
class Seed:
    id: str
    origin: str  # "refactors" | "tamper"
    prod_bug: dict[str, bytes]
    prod_good: dict[str, bytes] | None
    tests: dict[str, str]
    main_test: str
    modules: set[str]
    extras: dict[str, str | bytes] = field(default_factory=lambda: {"pytest.ini": BASELINE_INI})
    checks: dict[str, bool] = field(default_factory=dict)
    synthetic_ini: bool = True

    @property
    def honest_capable(self) -> bool:
        return self.prod_good is not None

    def main_source(self) -> str:
        return self.tests[self.main_test]


def _prod(root: Path, prefix: str = "") -> dict[str, bytes]:
    return {prefix + path: data for path, data in seed_tree(root).items()}


def _suite(root: Path, *production: dict[str, bytes]) -> tuple[dict[str, str], dict[str, str | bytes], bool]:
    tests: dict[str, str] = {}
    extras: dict[str, str | bytes] = {}
    source = seed_tree(root)
    # Config/conftest operators need the effective baseline even when it lives
    # in a production fixture. A shared suite cannot faithfully model two
    # different startup configs; reject that seed instead of choosing one.
    startup = {path for tree in production for path in tree
               if path in CONFIG_NAMES or Path(path).name == "conftest.py"}
    for path in sorted(startup - source.keys()):
        values = {tree.get(path) for tree in production}
        if len(values) != 1:
            raise SeedInventoryError(f"seed production startup files disagree: {path}")
        source[path] = values.pop()
    for path, data in source.items():
        # Operators edit Python and pytest.ini as text. Decode bytes directly
        # so unchanged CRLF spellings survive a materialise/build_changes round trip.
        if path.endswith(".py") or path in CONFIG_NAMES:
            try:
                value = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SeedInventoryError(f"seed source/config is not UTF-8: {root / path}") from exc
        else:
            value = data
        if path.endswith(".py") and Path(path).name != "conftest.py":
            tests[path] = value
        else:
            # Existing conftests must be visible to append_extra, not overwritten
            # by an operator adding a new conftest at the same path.
            extras[path] = value
    if PADDING_PATH in tests or PADDING_PATH in extras or any(PADDING_PATH in tree for tree in production):
        raise SeedInventoryError(f"seed fixture occupies reserved padding path: {root / PADDING_PATH}")
    available = set(tests) | set(extras)
    for tree in production:
        available.update(tree)
    synthetic_ini = not (CONFIG_NAMES & available)
    if synthetic_ini:
        extras["pytest.ini"] = BASELINE_INI
    return tests, extras, synthetic_ini


def _modules(prod: dict[str, bytes]) -> set[str]:
    mods: set[str] = set()
    for path in prod:
        if not path.endswith(".py"):
            continue
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
    for case in fixture_cases(checkwash_root, "refactors"):
        good, bug, before = case / "PROD-GOOD", case / "PROD-BUG", case / "BEFORE"
        if not (good.is_dir() and bug.is_dir() and before.is_dir()):
            continue
        prod_good, prod_bug = _prod(good), _prod(bug)
        tests, extras, synthetic_ini = _suite(before, prod_good, prod_bug)
        main = _main_test(tests)
        if main is None:
            continue
        tests[PADDING_PATH] = PADDING
        seeds.append(
            Seed(
                id=f"refactors/{case.name}",
                origin="refactors",
                prod_bug=prod_bug,
                prod_good=prod_good,
                tests=tests,
                main_test=main,
                modules=_modules(prod_bug),
                extras=extras,
                synthetic_ini=synthetic_ini,
            )
        )
    for case in fixture_cases(checkwash_root, "tamper"):
        src, before = case / "src", case / "before"
        if not (src.is_dir() and before.is_dir()):
            continue
        prod_bug = _prod(src, "src/")
        tests, extras, synthetic_ini = _suite(before, prod_bug)
        main = _main_test(tests)
        if main is None:
            continue
        tests[PADDING_PATH] = PADDING
        seeds.append(
            Seed(
                id=f"tamper/{case.name}",
                origin="tamper",
                prod_bug=prod_bug,
                prod_good=None,
                tests=tests,
                main_test=main,
                modules=_modules(prod_bug),
                extras=extras,
                synthetic_ini=synthetic_ini,
            )
        )
    return seeds
