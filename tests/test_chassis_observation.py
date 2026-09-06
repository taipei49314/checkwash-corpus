"""A chassis observation must describe one bare pytest process."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from corpus.chassis.observe import observe
from corpus.stress.sandbox import pytest_env


@pytest.mark.parametrize(
    "exit_code,stdout,stderr,green,collected,passed,silent",
    [
        (0, b"collected 2 items\n", b"2 passed\n", "green", 2, 2, False),
        (1, b"collected 2 items\n1 failed, 1 passed\n", b"", "red", 2, 1, False),
        (2, b"", b"collection error\n", "red", None, None, False),
        (0, b"collected 1 item\n", b"", "green", 1, None, True),
        (5, b"collected 0 items\nno tests ran\n", b"", "red", 0, None, True),
        (-9, None, None, "red", None, None, False),
    ],
)
def test_observation_fields_share_one_pytest_result(
    tmp_path: Path, monkeypatch, exit_code, stdout, stderr, green, collected, passed, silent
):
    first = subprocess.CompletedProcess([], exit_code, stdout, stderr)
    # A later invocation has a different outcome. It must never be requested.
    later = subprocess.CompletedProcess([], 1 if exit_code == 0 else 0, b"9 passed\n", b"")
    run = Mock(side_effect=[first, later])
    monkeypatch.setattr(subprocess, "run", run)

    row = observe(tmp_path, python="chosen-python", timeout=17)

    run.assert_called_once_with(
        ["chosen-python", "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True,
        cwd=str(tmp_path.resolve()),
        env=pytest_env(tmp_path.resolve() / "src"),
        timeout=17,
    )
    assert row.ci_exit == exit_code
    assert row.ci_green == green
    assert row.collected == collected
    assert row.passed == passed
    assert row.silent_suite is silent
    assert row.harness_exit is None
    assert set(row.as_dict()) == {
        "ci_exit", "ci_green", "collected", "passed", "silent_suite", "silent_reason", "harness_exit"
    }


@pytest.mark.parametrize(
    "error,green,reason",
    [
        (subprocess.TimeoutExpired("pytest", 17), "timeout", "pytest timeout"),
        (OSError("cannot start pytest"), "error", "pytest error"),
    ],
)
def test_incomplete_pytest_is_one_consistent_observation(tmp_path: Path, monkeypatch, error, green, reason):
    (tmp_path / "run_tests.py").write_text("# harness exists\n", encoding="utf-8")
    run = Mock(side_effect=error)
    monkeypatch.setattr(subprocess, "run", run)

    row = observe(tmp_path, timeout=17)

    assert run.call_count == 1  # No second bare pytest and no harness on failure.
    assert row.as_dict() == {
        "ci_exit": -1,
        "ci_green": green,
        "collected": None,
        "passed": None,
        "silent_suite": False,
        "silent_reason": reason,
        "harness_exit": None,
    }


@pytest.mark.parametrize(
    "harness_result,expected",
    [
        (subprocess.CompletedProcess([], 1, b"0 passed\n", b""), 1),
        (subprocess.TimeoutExpired("run_tests.py", 17), None),
        (OSError("cannot start harness"), None),
    ],
)
def test_harness_outcome_is_separate_from_pytest(tmp_path: Path, monkeypatch, harness_result, expected):
    script = tmp_path / "run_tests.py"
    script.write_text("# separate harness\n", encoding="utf-8")
    pytest_result = subprocess.CompletedProcess([], 0, b"collected 2 items\n2 passed\n", b"")
    run = Mock(side_effect=[pytest_result, harness_result])
    monkeypatch.setattr(subprocess, "run", run)

    row = observe(tmp_path, python="chosen-python", timeout=17)

    assert run.call_count == 2  # One bare pytest observation plus the separate harness.
    assert run.call_args_list[0].args[0][1:3] == ["-m", "pytest"]
    assert run.call_args_list[1].args[0] == ["chosen-python", str(script.resolve())]
    assert run.call_args_list[1].kwargs["timeout"] == 17
    assert (row.ci_exit, row.ci_green, row.collected, row.passed, row.silent_suite) == (0, "green", 2, 2, False)
    assert row.harness_exit == expected
