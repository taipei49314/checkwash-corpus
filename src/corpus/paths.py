from __future__ import annotations

from pathlib import Path

from corpus.gitutil import clone_state, is_usable_clone

LAYOUT_CACHE = "cache"
LAYOUT_BENCH = "bench"
LAYOUTS = (LAYOUT_CACHE, LAYOUT_BENCH)

# Wave-0 ids that `greenwash bench --corpus DIR` looks up at DIR/<id>.
WAVE0_BENCH_IDS = ("attrs", "click", "flask", "httpx", "rich", "starlette")


def repo_root(start: str | Path | None = None) -> Path:
    cur = Path(start or Path.cwd()).resolve()
    for path in [cur, *cur.parents]:
        if (path / "catalog" / "CATALOG.json").is_file():
            return path
    raise FileNotFoundError(
        "not a checkwash-corpus checkout — no catalog/CATALOG.json above "
        f"{cur}. Clone https://github.com/taipei49314/checkwash-corpus"
    )


def catalog_path(root: Path) -> Path:
    return root / "catalog" / "CATALOG.json"


def clones_dir(root: Path) -> Path:
    return root / "clones"


def clone_dest(root: Path, source_id: str, wave: str, layout: str = LAYOUT_CACHE) -> Path:
    """Where fetch writes this source."""
    if layout not in LAYOUTS:
        raise ValueError(f"unknown layout {layout!r}; want {LAYOUTS}")
    if layout == LAYOUT_BENCH and wave == "wave0-published-fp":
        return root / source_id
    return clones_dir(root) / source_id


def clone_candidates(root: Path, source_id: str) -> list[Path]:
    """Lookup order: cache first, then bench-layout root/<id>."""
    return [clones_dir(root) / source_id, root / source_id]


def resolve_clone(root: Path, source_id: str) -> Path | None:
    for path in clone_candidates(root, source_id):
        if is_usable_clone(path, root):
            return path
    return None


def clone_path(root: Path, source_id: str) -> Path:
    """Preferred path: a usable clone if one exists, else the cache dest."""
    found = resolve_clone(root, source_id)
    if found is not None:
        return found
    return clones_dir(root) / source_id


def inspect_clone(root: Path, source_id: str) -> tuple[str, Path]:
    """Return (missing|broken|ok, path that was inspected)."""
    for path in clone_candidates(root, source_id):
        state = clone_state(path, root)
        if state == "ok":
            return "ok", path
        if state == "broken":
            return "broken", path
    return "missing", clones_dir(root) / source_id


def sweep_path(root: Path, source_id: str) -> Path:
    return root / "records" / "sweeps" / f"{source_id}.json"


def census_path(root: Path, source_id: str) -> Path:
    return root / "records" / "census" / f"{source_id}.json"


def prs_dir(root: Path, source_id: str) -> Path:
    return root / "records" / "prs" / source_id
