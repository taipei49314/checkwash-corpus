from __future__ import annotations

import shutil
from pathlib import Path

from corpus.cli import main
from corpus.jsonio import dump
from corpus.paths import catalog_path, repo_root
from corpus.validate import validate


def test_dirty_engine_grandfather_is_rejected(tmp_path: Path) -> None:
    catalog = catalog_path(repo_root())
    (tmp_path / "catalog").mkdir()
    shutil.copy(catalog, tmp_path / "catalog" / "CATALOG.json")
    (tmp_path / "records" / "sweeps").mkdir(parents=True)
    dump(
        tmp_path / "records" / "sweeps" / "attrs.json",
        {
            "catalog_id": "attrs",
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
            "engine": {"asset": "editable-unrecorded", "sha256": None},
        },
    )
    errors = validate(tmp_path)
    assert any("editable-unrecorded" in e for e in errors)


def test_field_run_adj_must_pair_blocked_set(tmp_path: Path) -> None:
    catalog = catalog_path(repo_root())
    (tmp_path / "catalog").mkdir()
    shutil.copy(catalog, tmp_path / "catalog" / "CATALOG.json")
    run = tmp_path / "records" / "field-runs" / "2026-09-01"
    (run / "adjudication").mkdir(parents=True)
    engine = {"asset": "greenwash.pyz", "sha256": "a" * 64, "tag": "v0.1.49"}
    dump(
        run / "aiohttp.json",
        {
            "commits_analysed": 200,
            "commits_blocked": 1,
            "engine_errors": 0,
            "blocked_commits": [{"commit": "c" * 40, "findings": []}],
            "corpus": {
                "newest_commit": "a" * 40,
                "oldest_commit": "b" * 40,
                "greenwash_version": "0.1.49",
            },
            "engine": engine,
            "field_run": "external-2026-09-01",
            "source_id": "aiohttp",
        },
    )
    dump(
        run / "adjudication" / "aiohttp.json",
        {
            "catalog_id": "aiohttp",
            "sweep_file": "records/field-runs/2026-09-01/aiohttp.json",
            "verdicts": [],
            "wave": "external-2026-09-01",
        },
    )
    dump(
        run / "MANIFEST.json",
        {
            "id": "external-2026-09-01",
            "commits_analysed": 200,
            "commits_blocked": 1,
            "engine_errors": 0,
            "engine": engine,
            "projects": 1,
        },
    )
    errors = validate(tmp_path)
    assert any("unadjudicated" in e for e in errors)


def test_posted_field_run_is_on_the_ledger() -> None:
    errors = validate()
    assert errors == [], errors
    assert main(["status"]) == 0
