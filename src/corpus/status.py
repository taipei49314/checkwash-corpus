from __future__ import annotations

from pathlib import Path

from corpus.catalog import Catalog
from corpus.gitutil import has_commit, is_git_repo
from corpus.paths import census_path, clone_path, prs_dir, sweep_path


def source_status(root: Path, catalog: Catalog, source_id: str) -> dict[str, object]:
    src = catalog.source(source_id)
    clone = clone_path(root, source_id)
    cloned = is_git_repo(clone)
    pin = (src.published_pin or {}).get("newest_commit") or ""
    pin_ok = bool(cloned and pin and has_commit(clone, pin)) if pin else cloned
    pr_count = 0
    pdir = prs_dir(root, source_id)
    if pdir.is_dir():
        pr_count = len(list(pdir.glob("*.json")))
    return {
        "id": src.id,
        "wave": src.wave,
        "include": src.include,
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
        if st["census"]:
            row["census"] += 1
        if st["sweep"]:
            row["sweeps"] += 1
        row["prs"] += int(st["prs"])
    return waves
