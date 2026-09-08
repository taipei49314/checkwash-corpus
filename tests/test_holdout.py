from __future__ import annotations

import shutil
from pathlib import Path

from corpus.catalog import load_catalog
from corpus.holdout import (
    HELD_OUT,
    draw,
    eligible,
    field_run_ids,
    iter_draw_dirs,
    load_draw,
    spent_elsewhere_ids,
    swept_ids,
    validate_draws,
)
from corpus.jsonio import dump
from corpus.paths import catalog_path, repo_root


def _skeleton(tmp_path: Path) -> Path:
    (tmp_path / "catalog").mkdir()
    shutil.copy(catalog_path(repo_root()), tmp_path / "catalog" / "CATALOG.json")
    return tmp_path


def test_recorded_draws_satisfy_the_contract() -> None:
    assert validate_draws(repo_root()) == []


def test_every_recorded_draw_is_labelled_and_reproducible() -> None:
    root = repo_root()
    dirs = iter_draw_dirs(root)
    assert dirs, "records/holdout must hold at least the 2026-09-08 draw"
    for draw_dir in dirs:
        record = load_draw(draw_dir)
        assert record["class"] == HELD_OUT
        assert record["engine"]["tag"], "a rate belongs to an engine version"
        selection = record["selection"]
        ids = sorted(s["id"] for s in record["sources"])
        assert draw(selection["pool"], len(ids), selection["seed"]) == ids


def test_the_2026_09_08_draw_pins_a_1800_commit_window() -> None:
    record = load_draw(repo_root() / "records" / "holdout" / "2026-09-08")
    assert record["window"]["total_commits"] == 1800
    assert record["window"]["commits_per_source"] == 300
    assert len(record["sources"]) == 6
    assert record["spent"] is False
    for source in record["sources"]:
        head = source["pinned_head"]
        assert len(head) == 40 and all(c in "0123456789abcdef" for c in head)


def test_prediction_states_a_direction_before_the_sweep() -> None:
    record = load_draw(repo_root() / "records" / "holdout" / "2026-09-08")
    prediction = record["prediction"]
    assert "worse" in prediction["direction"]
    assert prediction["named_mechanisms"], "rule 5 wants a falsifiable mechanism"


def test_eligibility_excludes_wave0_field_runs_and_swept_windows() -> None:
    root = repo_root()
    pool, excluded = eligible(root)
    catalog = load_catalog(root)
    wave0 = {s.id for s in catalog.sources if s.wave == "wave0-published-fp"}

    assert wave0.isdisjoint(pool)
    assert field_run_ids(root).isdisjoint(pool)
    assert swept_ids(root).isdisjoint(pool)
    assert spent_elsewhere_ids(root).isdisjoint(pool)
    for source_id in ("aiohttp", "pandas", "sqlalchemy"):
        assert "field run" in excluded[source_id]
    for source_id in ("boto3", "typer"):
        assert "swept" in excluded[source_id]


def test_a_sweep_recorded_outside_this_repo_disqualifies() -> None:
    # The 2026-09-08 exploratory external evaluation ran from a working directory
    # outside every repository. Nothing under records/sweeps or records/field-runs
    # names it, so eligibility has to read spent-elsewhere.json or it will call six
    # already-swept repositories held-out (which the first draw did).
    root = repo_root()
    pool, excluded = eligible(root)
    for source_id in ("django", "moto", "poetry", "pytest", "scrapy", "sentry-python"):
        assert source_id not in pool
        assert "elsewhere" in excluded[source_id]
    assert spent_elsewhere_ids(root) >= {"aiohttp", "scrapy", "typer"}


def test_a_drawn_source_cannot_be_drawn_again(tmp_path: Path) -> None:
    root = _skeleton(tmp_path)
    dump(
        root / "records" / "holdout" / "2026-01-01" / "DRAW.json",
        {"sources": [{"id": "scrapy", "pinned_head": "a" * 40}]},
    )
    pool, excluded = eligible(root)
    assert "scrapy" not in pool
    assert "earlier draw" in excluded["scrapy"]


def test_a_draw_that_does_not_reproduce_from_its_seed_fails(tmp_path: Path) -> None:
    root = _skeleton(tmp_path)
    dump(
        root / "records" / "holdout" / "2026-01-02" / "DRAW.json",
        {
            "class": HELD_OUT,
            "drawn_on": "2026-01-02",
            "engine": {"asset": "checkwash.pyz", "tag": "v0.3.2", "sha256": "0" * 64},
            "id": "holdout-2026-01-02",
            "measurement": {},
            "prediction": {},
            "selection": {"pool": ["moto", "poetry", "pytest", "ray"], "seed": "seed"},
            "sources": [
                {
                    "id": "moto",
                    "owner_repo": "getmoto/moto",
                    "pinned_head": "a" * 40,
                    "remote": "https://github.com/getmoto/moto",
                }
            ],
            "spent": False,
            "window": {},
        },
    )
    errors = validate_draws(root)
    assert any("do not reproduce" in e for e in errors)


def test_a_short_pinned_head_fails(tmp_path: Path) -> None:
    root = _skeleton(tmp_path)
    dump(
        root / "records" / "holdout" / "2026-01-03" / "DRAW.json",
        {
            "class": HELD_OUT,
            "drawn_on": "2026-01-03",
            "engine": {},
            "id": "holdout-2026-01-03",
            "measurement": {},
            "prediction": {},
            "selection": {"pool": ["moto"], "seed": "s"},
            "sources": [
                {
                    "id": "moto",
                    "owner_repo": "getmoto/moto",
                    "pinned_head": "abc123",
                    "remote": "https://github.com/getmoto/moto",
                }
            ],
            "spent": False,
            "window": {},
        },
    )
    assert any("40-hex" in e for e in validate_draws(root))
