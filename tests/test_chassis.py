"""Chassis arm (estate T-127): silent-suite is an extra column, not a new green.

Toy-seed `ci_green` stays returncode == 0. A collect-only / collected-0
suite is recorded as silent_suite=true without rewriting that oracle.
The replica is a public fake repo; universe-explorer itself is private
and is not vendored. This is not a T-83 probe seed.
"""

from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from corpus.chassis.observe import observe
from corpus.chassis.replica import replica_tree, write_replica
from corpus.chassis.silent_suite import classify_pytest
from corpus.cli import main
from corpus.stress import sandbox

ROOT = Path(__file__).resolve().parents[1]
PYZ = ROOT / "checkwash.pyz"
FIXTURE = ROOT / "fixtures" / "chassis" / "collect_only"
CI_GREEN_RETURN = 'return "green" if proc.returncode == 0 else "red"'


def test_ci_green_oracle_is_still_exit_zero():
    src = inspect.getsource(sandbox.ci_green)
    assert CI_GREEN_RETURN in src
    assert "silent_suite" not in src


def test_collected_zero_exit_zero_is_silent_without_redefining_green():
    row = classify_pytest("collected 0 items\n", returncode=0)
    assert row.silent_suite is True
    assert row.collected == 0
    assert CI_GREEN_RETURN in inspect.getsource(sandbox.ci_green)


def test_collect_only_replica_is_ci_green_and_silent_suite(tmp_path: Path):
    root = write_replica(tmp_path / "collect_only", "collect_only")
    obs = observe(root)
    assert obs.ci_exit == 0
    assert obs.ci_green == "green"
    assert obs.silent_suite is True
    assert obs.harness_exit == 1
    assert CI_GREEN_RETURN in inspect.getsource(sandbox.ci_green)


def test_passing_replica_is_green_and_not_silent(tmp_path: Path):
    root = write_replica(tmp_path / "passing", "passing")
    obs = observe(root)
    assert obs.ci_exit == 0
    assert obs.ci_green == "green"
    assert obs.silent_suite is False
    assert obs.passed == 1
    assert obs.harness_exit == 0


def test_collect_zero_is_silent_and_leaves_ci_green_to_the_exit_oracle(tmp_path: Path):
    root = write_replica(tmp_path / "collect_zero", "collect_zero")
    obs = observe(root)
    assert obs.silent_suite is True
    expected = "green" if obs.ci_exit == 0 else "red"
    assert obs.ci_green == expected
    if obs.ci_exit != 0:
        assert obs.ci_green != "green"


def test_committed_fixture_matches_replica_and_is_silent_green():
    assert FIXTURE.is_dir(), "public replica must be in git"
    obs = observe(FIXTURE)
    assert obs.ci_green == "green"
    assert obs.ci_exit == 0
    assert obs.silent_suite is True
    tree = replica_tree("collect_only")
    for path, data in tree.items():
        assert (FIXTURE / path).read_bytes().replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n")


def test_cli_observe_prints_columns(tmp_path: Path, capsys):
    root = write_replica(tmp_path / "cli", "collect_only")
    assert main(["chassis", "observe", str(root)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ci_green"] == "green"
    assert payload["silent_suite"] is True
    assert payload["ci_exit"] == 0


def test_cli_materialise(tmp_path: Path):
    dest = tmp_path / "out"
    assert main(["chassis", "materialise", str(dest), "--kind", "passing"]) == 0
    obs = observe(dest)
    assert obs.ci_green == "green"
    assert obs.silent_suite is False


@pytest.mark.skipif(not PYZ.exists(), reason="needs the release zipapp at the repository root")
def test_cli_vs_embedded_parity_on_replica(tmp_path: Path):
    # Engine() pins checkwash from the pyz into sys.modules. Run in a child
    # so later tests can still construct their own Engine.
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    work = tmp_path / "bb"
    code = "\n".join([
        "from pathlib import Path",
        "from corpus.chassis.parity import check_parity",
        "from corpus.chassis.replica import TEST_ADD, replica_tree",
        f"pyz = Path({str(PYZ)!r})",
        "before = replica_tree('passing')",
        "after = dict(before)",
        "after['tests/test_add.py'] = TEST_ADD.replace('assert add(1, 1) == 2', 'assert True').encode()",
        f"r = check_parity(pyz, before, after, Path({str(work)!r}))",
        "assert r.cli is not None and r.embedded is not None",
        "assert r.divergence is False, (r.embedded, r.cli, r.note)",
        "print(r.embedded, r.cli)",
    ])
    proc = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
