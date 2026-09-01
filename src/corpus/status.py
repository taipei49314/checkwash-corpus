from __future__ import annotations

from pathlib import Path

from corpus.catalog import Catalog
from corpus.field_run import field_run_row, iter_field_run_dirs
from corpus.gitutil import has_commit
from corpus.paths import census_path, inspect_clone, prs_dir, resolve_clone, sweep_path


def source_status(root: Path, catalog: Catalog, source_id: str) -> dict[str, object]:
    src = catalog.source(source_id)
    state, path = inspect_clone(root, source_id)
    cloned = state == "ok"
    pin = (src.published_pin or {}).get("newest_commit") or ""
    repo = resolve_clone(root, source_id)
    pin_ok = bool(cloned and pin and repo is not None and has_commit(repo, pin)) if pin else cloned
    pr_count = 0
    pdir = prs_dir(root, source_id)
    if pdir.is_dir():
        pr_count = len(list(pdir.glob("*.json")))
    return {
        "id": src.id,
        "wave": src.wave,
        "include": src.include,
        "clone_state": state,
        "clone_path": str(path),
        "cloned": cloned,
        "pin_present": pin_ok,
        "census": census_path(root, source_id).is_file(),
        "sweep": sweep_path(root, source_id).is_file(),
        "prs": pr_count,
    }


def wave_status(root: Path, catalog: Catalog) -> dict[str, dict[str, int]]:
    waves: dict[str, dict[str, int]] = {}
    for wave_id in catalog.waves:
        waves[wave_id] = {
            "catalogued": 0,
            "included": 0,
            "cloned": 0,
            "broken": 0,
            "census": 0,
            "sweeps": 0,
            "prs": 0,
        }
    for src in catalog.sources:
        row = waves[src.wave]
        row["catalogued"] += 1
        if src.include:
            row["included"] += 1
        st = source_status(root, catalog, src.id)
        if st["cloned"]:
            row["cloned"] += 1
        if st["clone_state"] == "broken":
            row["broken"] += 1
        if st["census"]:
            row["census"] += 1
        if st["sweep"]:
            row["sweeps"] += 1
        row["prs"] += int(st["prs"])
    return waves


def field_run_status(root: Path) -> list[dict[str, object]]:
    return [field_run_row(path) for path in iter_field_run_dirs(root)]
