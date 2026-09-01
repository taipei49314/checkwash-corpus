from __future__ import annotations

from pathlib import Path


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


def clone_path(root: Path, source_id: str) -> Path:
    return clones_dir(root) / source_id


def sweep_path(root: Path, source_id: str) -> Path:
    return root / "records" / "sweeps" / f"{source_id}.json"


def census_path(root: Path, source_id: str) -> Path:
    return root / "records" / "census" / f"{source_id}.json"


def prs_dir(root: Path, source_id: str) -> Path:
    return root / "records" / "prs" / source_id
