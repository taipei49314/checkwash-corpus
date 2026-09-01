from __future__ import annotations

from pathlib import Path

from corpus.catalog import load_catalog, validate_raw
from corpus.engine import PYZ_ASSETS
from corpus.jsonio import load
from corpus.paths import catalog_path, census_path, repo_root

SWEEP_REQUIRED = (
    "catalog_id",
    "wave",
    "commits_analysed",
    "commits_blocked",
    "engine_errors",
)
CENSUS_REQUIRED = ("catalog_id", "wave", "revision", "probes", "counts")
ADJ_CATEGORIES = {"false_positive", "spec_correct", "unclear"}
GRANDFATHER_DIRTY = "editable-unrecorded"


def _engine_errors(path_name: str, wave: str, engine: object) -> list[str]:
    if not isinstance(engine, dict):
        return [f"{path_name}: missing engine asset record"]
    asset = engine.get("asset")
    sha = engine.get("sha256")
    if asset in PYZ_ASSETS:
        if not (isinstance(sha, str) and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)):
            return [f"{path_name}: {asset} requires a 64-hex sha256"]
        return []
    if asset == GRANDFATHER_DIRTY:
        if wave != "wave0-published-fp":
            return [
                f"{path_name}: editable-unrecorded is only allowed on the "
                "2026-09-01 wave0 reproduction"
            ]
        return []
    return [
        f"{path_name}: engine asset {asset!r} cannot be published "
        "(need checkwash.pyz / greenwash.pyz, or the wave0 grandfather)"
    ]


def validate(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    errors: list[str] = []
    raw = load(catalog_path(root))
    errors.extend(validate_raw(raw))
    try:
        catalog = load_catalog(root)
    except ValueError as exc:
        return errors + [str(exc)]

    ids = {s.id: s for s in catalog.sources}
    for path in sorted((root / "records" / "sweeps").glob("*.json")):
        data = load(path)
        for key in SWEEP_REQUIRED:
            if key not in data:
                errors.append(f"{path.name}: missing {key}")
        corpus = data.get("corpus") or {}
        if not corpus.get("newest_commit") or not corpus.get("oldest_commit"):
            errors.append(f"{path.name}: corpus pins missing")
        if not (corpus.get("greenwash_version") or corpus.get("checkwash_version")):
            errors.append(f"{path.name}: engine version missing")
        cid = data.get("catalog_id")
        wave = data.get("wave") or ""
        if cid and cid not in ids:
            errors.append(f"{path.name}: catalog_id {cid!r} is not in the catalog")
        if cid and path.stem != cid:
            errors.append(f"{path.name}: filename stem != catalog_id {cid!r}")
        errors.extend(_engine_errors(path.name, str(wave), data.get("engine")))
        if wave == "wave1-mock-power" and cid:
            if not census_path(root, str(cid)).is_file():
                errors.append(
                    f"{path.name}: wave1 sweep has no records/census/{cid}.json "
                    "(SPEC: power before precision)"
                )

    for path in sorted((root / "records" / "census").glob("*.json")):
        data = load(path)
        for key in CENSUS_REQUIRED:
            if key not in data:
                errors.append(f"census/{path.name}: missing {key}")
        cid = data.get("catalog_id")
        if cid and cid not in ids:
            errors.append(f"census/{path.name}: catalog_id {cid!r} is not in the catalog")
        if cid and path.stem != cid:
            errors.append(f"census/{path.name}: filename stem != catalog_id {cid!r}")
        probes = data.get("probes") or {}
        for key in ("patch", "unittest_assert", "approx", "skip"):
            if key not in probes:
                errors.append(f"census/{path.name}: probes missing {key}")

    for path in sorted((root / "adjudication").glob("*.json")):
        if path.name == "TEMPLATE.json":
            continue
        data = load(path)
        cid = data.get("catalog_id")
        sweep_file = data.get("sweep_file")
        if not cid or not sweep_file:
            errors.append(f"adjudication/{path.name}: need catalog_id and sweep_file")
            continue
        sweep_path = root / sweep_file
        if not sweep_path.is_file():
            errors.append(f"adjudication/{path.name}: sweep_file {sweep_file} does not exist")
            continue
        sweep = load(sweep_path)
        blocked = {row.get("commit") for row in sweep.get("blocked_commits") or []}
        judged = {row.get("commit") for row in data.get("verdicts") or []}
        extra = judged - blocked
        missing = blocked - judged
        if extra:
            errors.append(f"adjudication/{path.name}: commits not in sweep: {sorted(extra)[:5]}")
        if missing:
            errors.append(f"adjudication/{path.name}: sweep blocks unadjudicated: {sorted(missing)[:5]}")
        for row in data.get("verdicts") or []:
            cat = row.get("category")
            if cat not in ADJ_CATEGORIES:
                errors.append(f"adjudication/{path.name}: bad category {cat!r}")
    return errors
