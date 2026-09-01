from __future__ import annotations

import shutil
from pathlib import Path

from corpus.jsonio import dump
from corpus.paths import catalog_path, repo_root
from corpus.validate import validate


def test_wave1_sweep_without_census_is_invalid(tmp_path: Path) -> None:
    catalog = catalog_path(repo_root())
    (tmp_path / "catalog").mkdir()
    shutil.copy(catalog, tmp_path / "catalog" / "CATALOG.json")
    (tmp_path / "records" / "sweeps").mkdir(parents=True)
    dump(
        tmp_path / "records" / "sweeps" / "airflow.json",
        {
            "catalog_id": "airflow",
            "wave": "wave1-mock-power",
            "commits_analysed": 1,
            "commits_blocked": 0,
            "engine_errors": 0,
            "blocked_commits": [],
            "corpus": {
                "newest_commit": "a" * 40,
                "oldest_commit": "b" * 40,
                "checkwash_version": "0.2.1",
            },
            "engine": {
                "asset": "checkwash.pyz",
                "sha256": "c" * 64,
            },
        },
    )
    errors = validate(tmp_path)
    assert any("census" in e and "airflow" in e for e in errors)


def test_pyz_engine_without_sha_is_invalid(tmp_path: Path) -> None:
    catalog = catalog_path(repo_root())
    (tmp_path / "catalog").mkdir()
    shutil.copy(catalog, tmp_path / "catalog" / "CATALOG.json")
    (tmp_path / "records" / "sweeps").mkdir(parents=True)
    dump(
        tmp_path / "records" / "sweeps" / "flask.json",
        {
            "catalog_id": "flask",
            "wave": "wave0-published-fp",
            "commits_analysed": 1,
            "commits_blocked": 0,
            "engine_errors": 0,
            "blocked_commits": [],
            "corpus": {
                "newest_commit": "a" * 40,
                "oldest_commit": "b" * 40,
                "checkwash_version": "0.1.49",
            },
            "engine": {"asset": "checkwash.pyz", "sha256": None},
        },
    )
    errors = validate(tmp_path)
    assert any("sha256" in e for e in errors)
