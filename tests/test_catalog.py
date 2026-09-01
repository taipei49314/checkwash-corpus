from __future__ import annotations

from corpus.catalog import WAVE0_REMOTES, load_catalog, validate_raw
from corpus.jsonio import load
from corpus.paths import catalog_path, repo_root


def test_catalog_loads_and_validates() -> None:
    root = repo_root()
    errors = validate_raw(load(catalog_path(root)))
    assert errors == []
    catalog = load_catalog(root)
    assert catalog.schema_version == 1
    assert len(catalog.sources) >= 26


def test_wave0_remotes_match_greenwash_bench() -> None:
    catalog = load_catalog(repo_root())
    wave0 = {s.id: s.remote for s in catalog.sources if s.wave == "wave0-published-fp"}
    assert wave0 == WAVE0_REMOTES
    for src in catalog.sources:
        if src.wave == "wave0-published-fp":
            assert src.include is True
            assert src.published_pin
            assert src.published_pin.get("newest_commit")
            assert src.published_pin.get("oldest_commit")


def test_ids_and_remotes_unique() -> None:
    catalog = load_catalog(repo_root())
    ids = [s.id for s in catalog.sources]
    remotes = [s.remote for s in catalog.sources]
    assert len(ids) == len(set(ids))
    assert len(remotes) == len(set(remotes))


def test_planned_filtered_unless_asked() -> None:
    catalog = load_catalog(repo_root())
    included = catalog.select(wave="wave2-js-oracle")
    assert included == []
    planned = catalog.select(wave="wave2-js-oracle", include_planned=True)
    assert {s.id for s in planned} == {"axios", "express", "vitest"}


def test_select_unknown_id_errors() -> None:
    catalog = load_catalog(repo_root())
    try:
        catalog.select(source_id="not-a-source")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_wave1_is_the_expansion_twenty() -> None:
    catalog = load_catalog(repo_root())
    wave1 = [s.id for s in catalog.sources if s.wave == "wave1-mock-power"]
    assert len(wave1) == 20
    assert "airflow" in wave1
    assert "django" in wave1
    assert all(s.include for s in catalog.sources if s.wave == "wave1-mock-power")
