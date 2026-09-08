"""Held-out draws live under records/holdout/<date>/DRAW.json.

SPEC section 10 splits every published false-positive rate into two classes.
A tuning-corpus (in-sample) rate says how often checkwash blocks the
repositories its detectors were shaped on. A held-out rate says how often it
blocks repositories nobody looked at first, and it only means that if the
draw was recorded before the engine ran.

This module owns the eligibility arithmetic so the claim can fail a test
rather than rest on prose. Eligibility is derived from what is on disk --
the catalog, the sweep records, the field-run ledgers and any earlier draw --
never from a hand-maintained exclusion list.
"""

from __future__ import annotations

import random
from pathlib import Path

from corpus.field_run import iter_field_run_dirs, sweep_paths
from corpus.jsonio import load
from corpus.paths import repo_root

DRAW_NAME = "DRAW.json"
HELD_OUT = "held-out"
IN_SAMPLE = "in-sample"

# Only wave1 was catalogued as unspent reserve. Wave 0 is in-sample since
# 2026-07-30; wave 2 is planned and not fetched.
ELIGIBLE_WAVE = "wave1-mock-power"

DRAW_REQUIRED = (
    "class",
    "drawn_on",
    "engine",
    "id",
    "measurement",
    "prediction",
    "selection",
    "sources",
    "spent",
    "window",
)
SOURCE_REQUIRED = ("id", "owner_repo", "pinned_head", "remote")


def holdout_root(root: Path) -> Path:
    return root / "records" / "holdout"


def iter_draw_dirs(root: Path) -> list[Path]:
    base = holdout_root(root)
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir() and (p / DRAW_NAME).is_file())


def load_draw(draw_dir: Path) -> dict:
    return load(draw_dir / DRAW_NAME)


def swept_ids(root: Path) -> set[str]:
    """Ids with a recorded sweep window. SPEC 10.1 makes those in-sample."""
    base = root / "records" / "sweeps"
    if not base.is_dir():
        return set()
    return {p.stem for p in base.glob("*.json")}


def field_run_ids(root: Path) -> set[str]:
    """Ids appearing in any field-run ledger. SPEC 10.1 names these spent."""
    ids: set[str] = set()
    for run_dir in iter_field_run_dirs(root):
        ids.update(p.stem for p in sweep_paths(run_dir))
    return ids


def drawn_ids(root: Path) -> set[str]:
    """Ids consumed by an earlier draw. SPEC 10.2 rule 2 bars re-drawing."""
    ids: set[str] = set()
    for draw_dir in iter_draw_dirs(root):
        for source in load_draw(draw_dir).get("sources", []):
            if isinstance(source, dict) and source.get("id"):
                ids.add(str(source["id"]))
    return ids


def eligible(root: Path | None = None, catalog=None) -> tuple[list[str], dict[str, str]]:
    """Return (sorted eligible ids, {excluded id: reason})."""
    root = root or repo_root()
    if catalog is None:
        from corpus.catalog import load_catalog

        catalog = load_catalog(root)

    swept = swept_ids(root)
    field = field_run_ids(root)
    already = drawn_ids(root)

    keep: list[str] = []
    excluded: dict[str, str] = {}
    for source in catalog.sources:
        if source.wave != ELIGIBLE_WAVE:
            excluded[source.id] = f"wave {source.wave} is not held-out reserve"
        elif source.id in field:
            excluded[source.id] = "spent by a field run (SPEC 10.1)"
        elif source.id in swept:
            excluded[source.id] = "a window of its history was swept (SPEC 10.1)"
        elif source.id in already:
            excluded[source.id] = "consumed by an earlier draw (SPEC 10.2 rule 2)"
        else:
            keep.append(source.id)
    return sorted(keep), excluded


def draw(pool: list[str], count: int, seed: str) -> list[str]:
    """Uniform sample without replacement. Deterministic in (pool, count, seed)."""
    ordered = sorted(pool)
    if count > len(ordered):
        raise ValueError(f"cannot draw {count} from a pool of {len(ordered)}")
    return sorted(random.Random(seed).sample(ordered, count))


def validate_draws(root: Path) -> list[str]:
    """Contract errors across every recorded draw."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    for draw_dir in iter_draw_dirs(root):
        label = f"records/holdout/{draw_dir.name}/{DRAW_NAME}"
        record = load_draw(draw_dir)
        for key in DRAW_REQUIRED:
            if key not in record:
                errors.append(f"{label}: missing {key}")
        if record.get("class") not in (HELD_OUT, IN_SAMPLE):
            errors.append(f"{label}: class must be {HELD_OUT!r} or {IN_SAMPLE!r}")

        selection = record.get("selection")
        if isinstance(selection, dict):
            pool = selection.get("pool")
            seed = selection.get("seed")
            ids = [s.get("id") for s in record.get("sources", []) if isinstance(s, dict)]
            if isinstance(pool, list) and isinstance(seed, str) and ids:
                want = draw(list(pool), len(ids), seed)
                if want != sorted(str(i) for i in ids):
                    errors.append(
                        f"{label}: sources do not reproduce from (pool, seed); "
                        f"recorded {sorted(str(i) for i in ids)}, recomputed {want}"
                    )
        else:
            errors.append(f"{label}: selection must be an object")

        for source in record.get("sources", []):
            if not isinstance(source, dict):
                errors.append(f"{label}: source entries must be objects")
                continue
            for key in SOURCE_REQUIRED:
                if not source.get(key):
                    errors.append(f"{label}: source {source.get('id')!r} missing {key}")
            head = source.get("pinned_head")
            if isinstance(head, str) and not (
                len(head) == 40 and all(c in "0123456789abcdef" for c in head)
            ):
                errors.append(f"{label}: source {source.get('id')!r} pinned_head must be a 40-hex sha")
            prior = seen.get(str(source.get("id")))
            if prior:
                errors.append(f"{label}: {source.get('id')!r} was already drawn in {prior}")
            else:
                seen[str(source.get("id"))] = draw_dir.name
    return errors
