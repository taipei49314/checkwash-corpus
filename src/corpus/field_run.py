"""Field-run ledgers live under records/field-runs/, not records/sweeps/.

They are copied engine JSON, not catalogued wave members. Mixing them into
wave0/wave1 aggregates is a SPEC violation.
"""

from __future__ import annotations

from pathlib import Path

from corpus.jsonio import load

MANIFEST_NAME = "MANIFEST.json"


def field_runs_root(root: Path) -> Path:
    return root / "records" / "field-runs"


def iter_field_run_dirs(root: Path) -> list[Path]:
    base = field_runs_root(root)
    if not base.is_dir():
        return []
    return sorted(
        path
        for path in base.iterdir()
        if path.is_dir() and (path / MANIFEST_NAME).is_file()
    )


def sweep_paths(run_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in run_dir.glob("*.json")
        if path.name != MANIFEST_NAME
    )


def adj_path(run_dir: Path, source_id: str) -> Path:
    return run_dir / "adjudication" / f"{source_id}.json"


def load_manifest(run_dir: Path) -> dict:
    return load(run_dir / MANIFEST_NAME)


def field_run_row(run_dir: Path) -> dict[str, object]:
    manifest = load_manifest(run_dir)
    sweeps = sweep_paths(run_dir)
    judged = 0
    for path in sweeps:
        if adj_path(run_dir, path.stem).is_file():
            judged += 1
    return {
        "id": manifest.get("id") or run_dir.name,
        "sweeps": len(sweeps),
        "adjudicated": judged,
        "commits_analysed": int(manifest.get("commits_analysed") or 0),
        "commits_blocked": int(manifest.get("commits_blocked") or 0),
        "engine_errors": int(manifest.get("engine_errors") or 0),
    }
