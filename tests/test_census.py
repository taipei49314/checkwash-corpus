from __future__ import annotations

import subprocess
from pathlib import Path

from corpus.catalog import load_catalog
from corpus.census import census_clone


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_census_counts_patch_and_unittest(tmp_path: Path) -> None:
    repo = tmp_path / "toy"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_toy.py").write_text(
        "from unittest import mock\n"
        "from unittest.mock import patch\n"
        "\n"
        "def test_a(monkeypatch):\n"
        "    with mock.patch('toy.fn'):\n"
        "        assert 1 == 1\n"
        "    patch.object(toy, 'fn', lambda: 1)\n"
        "    monkeypatch.setattr(toy, 'fn', lambda: 1)\n"
        "\n"
        "class T:\n"
        "    def test_b(self):\n"
        "        self.assertEqual(1, 1)\n"
        "        self.assertTrue(True)\n",
        encoding="utf-8",
    )
    (repo / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init")
    catalog = load_catalog()
    source = catalog.source("flask")
    record = census_clone(repo, source, catalog, "HEAD")
    counts = record["counts"]
    assert counts["patch_sites"] >= 2
    assert counts["unittest_asserts"] >= 2
    assert counts["runner_files"] >= 1
    assert record["probes"]["patch"] == catalog.power_probes["patch"]
