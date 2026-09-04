"""Record ci_green and silent_suite as separate columns.

`ci_green` is imported from the stress sandbox and not reimplemented. A
silent suite must not flip that oracle to red.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from corpus.chassis.silent_suite import classify_pytest
from corpus.stress.sandbox import ci_green, pytest_env

PYTEST_ARGV = ["-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"]


@dataclass(frozen=True)
class ChassisObservation:
    ci_exit: int
    ci_green: str
    collected: int | None
    passed: int | None
    silent_suite: bool
    silent_reason: str
    harness_exit: int | None

    def as_dict(self) -> dict:
        return asdict(self)


def _pytest_proc(root: Path, python: str | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    argv = [python or sys.executable, *PYTEST_ARGV]
    return subprocess.run(
        argv,
        capture_output=True,
        cwd=str(root),
        env=pytest_env(root / "src"),
        timeout=timeout,
    )


def _harness_exit(root: Path, python: str | None = None, timeout: int = 60) -> int | None:
    script = root / "run_tests.py"
    if not script.is_file():
        return None
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [python or sys.executable, str(script)],
        capture_output=True,
        cwd=str(root),
        env=env,
        timeout=timeout,
    )
    return int(proc.returncode)


def observe(root: Path, python: str | None = None, timeout: int = 60) -> ChassisObservation:
    root = root.resolve()
    green = ci_green(root, python=python, timeout=timeout)
    try:
        proc = _pytest_proc(root, python=python, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ChassisObservation(-1, green, None, None, False, "pytest timeout", None)
    except OSError:
        return ChassisObservation(-1, green, None, None, False, "pytest error", None)
    out = ((proc.stdout or b"") + b"\n" + (proc.stderr or b"")).decode("utf-8", "replace")
    census = classify_pytest(out, proc.returncode)
    try:
        harness = _harness_exit(root, python=python, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        harness = None
    return ChassisObservation(
        ci_exit=proc.returncode,
        ci_green=green,
        collected=census.collected,
        passed=census.passed,
        silent_suite=census.silent_suite,
        silent_reason=census.reason,
        harness_exit=harness,
    )
