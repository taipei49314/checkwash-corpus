"""Mini public replica of a universe-explorer-style `run_tests` harness.

The science repo is private and must not be vendored. This tree is a fake
app plus the silent-suite gate rules, small enough for corpus CI.
"""

from __future__ import annotations

from pathlib import Path

from corpus.stress.sandbox import materialise

ADD_PY = "def add(a, b):\n    return a + b\n"
TEST_ADD = (
    "from app.add import add\n"
    "\n"
    "\n"
    "def test_add():\n"
    "    assert add(1, 1) == 2\n"
)
TEST_EMPTY = "# no test functions — pytest collects 0 items\n"
INI_PASSING = "[pytest]\ntestpaths = tests\npythonpath = src\n"
INI_COLLECT_ONLY = "[pytest]\ntestpaths = tests\npythonpath = src\naddopts = --collect-only\n"
INIT_PY = ""

# Methodology copy of universe-explorer/run_tests.py silent-suite rules.
# Not a byte-for-byte vendor of that file (private repo, science content).
RUN_TESTS_PY = '''"""Replica silent-suite gate. Exit 0 is not enough if nothing ran."""
from __future__ import annotations

import re
import subprocess
import sys

_PASSED_RE = re.compile(r"(\\d+)\\s+passed")


def _run_suite(suite: str) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", suite, "-q", "--tb=line"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = ((r.stdout or "") + "\\n" + (r.stderr or "")).strip()
    low = out.lower()
    if "no tests ran" in low or re.search(r"collected 0 items", low):
        return 1, "FAIL collected 0 items (silent suite)"
    m = _PASSED_RE.search(out)
    n_pass = int(m.group(1)) if m else None
    if r.returncode == 0 and n_pass == 0:
        return 1, "FAIL 0 passed (silent suite)"
    if r.returncode == 0 and n_pass is None and "passed" not in low:
        return 1, "FAIL no pytest summary (silent suite)"
    tail = out.splitlines()[-1] if out.splitlines() else "(no output)"
    if r.returncode != 0:
        return r.returncode, tail
    return 0, tail if n_pass is None else f"{n_pass} passed"


def main() -> int:
    code, tail = _run_suite("tests")
    mark = "ok " if code == 0 else "FAIL"
    print(f"  {mark} tests  {tail}")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

KINDS = ("passing", "collect_only", "collect_zero")


def replica_files(kind: str) -> tuple[dict[str, bytes], dict[str, str], dict[str, str]]:
    """(prod, tests, extras) for sandbox.materialise."""
    if kind not in KINDS:
        raise ValueError(f"unknown replica kind {kind!r}; want {KINDS}")
    prod = {
        "src/app/__init__.py": INIT_PY.encode("utf-8"),
        "src/app/add.py": ADD_PY.encode("utf-8"),
    }
    extras = {"run_tests.py": RUN_TESTS_PY}
    if kind == "passing":
        return prod, {"tests/test_add.py": TEST_ADD}, {**extras, "pytest.ini": INI_PASSING}
    if kind == "collect_only":
        return prod, {"tests/test_add.py": TEST_ADD}, {**extras, "pytest.ini": INI_COLLECT_ONLY}
    return prod, {"tests/test_empty.py": TEST_EMPTY}, {**extras, "pytest.ini": INI_PASSING}


def replica_tree(kind: str) -> dict[str, bytes]:
    prod, tests, extras = replica_files(kind)
    tree = dict(prod)
    for path, text in tests.items():
        tree[path] = text.encode("utf-8") if isinstance(text, str) else text
    for path, text in extras.items():
        tree[path] = text.encode("utf-8")
    return tree


def write_replica(root: Path, kind: str) -> Path:
    prod, tests, extras = replica_files(kind)
    materialise(root, prod, tests, extras)
    return root
