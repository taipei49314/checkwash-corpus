"""Classify pytest output the way universe-explorer `run_tests.py` does.

A collected-0 / 0-passed / summary-less exit 0 is a silent suite. That is
not the same as `ci_green`: the toy-seed oracle is still returncode == 0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PASSED_RE = re.compile(r"(\d+)\s+passed")
_COLLECTED_RE = re.compile(r"collected\s+(\d+)\s+item")


@dataclass(frozen=True)
class PytestCensus:
    returncode: int
    collected: int | None
    passed: int | None
    silent_suite: bool
    reason: str


def classify_pytest(output: str, returncode: int) -> PytestCensus:
    """Parse one pytest invocation. `silent_suite` does not rewrite green."""
    text = (output or "").strip()
    low = text.lower()
    collected_m = _COLLECTED_RE.search(low)
    collected = int(collected_m.group(1)) if collected_m else None
    passed_m = _PASSED_RE.search(text)
    passed = int(passed_m.group(1)) if passed_m else None

    if "no tests ran" in low or collected == 0:
        return PytestCensus(returncode, collected, passed, True, "collected 0 or no tests ran")
    if returncode == 0 and passed == 0:
        return PytestCensus(returncode, collected, passed, True, "0 passed")
    if returncode == 0 and passed is None and "passed" not in low:
        return PytestCensus(returncode, collected, passed, True, "no pytest summary")
    return PytestCensus(returncode, collected, passed, False, "")
