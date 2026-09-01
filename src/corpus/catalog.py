from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from corpus.jsonio import load
from corpus.paths import catalog_path, repo_root

REQUIRED_SOURCE_KEYS = (
    "id",
    "wave",
    "remote",
    "owner_repo",
    "license",
    "test_paths",
    "include",
    "why",
)

# Remotes greenwash bench.py already hard-codes. Wave 0 must not drift.
WAVE0_REMOTES = {
    "attrs": "https://github.com/python-attrs/attrs",
    "click": "https://github.com/pallets/click",
    "flask": "https://github.com/pallets/flask",
    "httpx": "https://github.com/encode/httpx",
    "rich": "https://github.com/Textualize/rich",
    "starlette": "https://github.com/encode/starlette",
}


@dataclass(frozen=True)
class Wave:
    id: str
    purpose: str
    commit_limit: int
    clone_depth: int


@dataclass(frozen=True)
class Source:
    id: str
    wave: str
    remote: str
    owner_repo: str
    license: str
    test_paths: tuple[str, ...]
    include: bool
    why: str
    published_pin: dict[str, str] | None
    prior_power: dict[str, Any] | None
    raw: dict[str, Any]


@dataclass
class Catalog:
    schema_version: int
    engine_repo: str
    purpose: str
    waves: dict[str, Wave]
    sources: list[Source]
    power_probes: dict[str, Any]
    raw: dict[str, Any]

    def source(self, source_id: str) -> Source:
        for item in self.sources:
            if item.id == source_id:
                return item
        raise KeyError(f"unknown catalog id: {source_id}")

    def select(
        self,
        *,
        wave: str | None = None,
        source_id: str | None = None,
        include_planned: bool = False,
    ) -> list[Source]:
        out: list[Source] = []
        for item in self.sources:
            if source_id and item.id != source_id:
                continue
            if wave and item.wave != wave:
                continue
            if not item.include and not include_planned:
                continue
            out.append(item)
        if source_id and not out:
            # Named id is always an error if it exists but was filtered,
            # and a different error if it does not exist at all.
            try:
                item = self.source(source_id)
            except KeyError:
                raise
            raise ValueError(
                f"{source_id} is catalogued as planned (include=false); "
                "pass --include-planned to fetch or measure it"
            )
        return out


def _as_wave(wid: str, data: dict[str, Any]) -> Wave:
    return Wave(
        id=wid,
        purpose=str(data["purpose"]),
        commit_limit=int(data["commit_limit"]),
        clone_depth=int(data["clone_depth"]),
    )


def _as_source(data: dict[str, Any]) -> Source:
    missing = [k for k in REQUIRED_SOURCE_KEYS if k not in data]
    if missing:
        raise ValueError(f"source missing keys {missing}: {data.get('id')}")
    pin = data.get("published_pin")
    return Source(
        id=str(data["id"]),
        wave=str(data["wave"]),
        remote=str(data["remote"]),
        owner_repo=str(data["owner_repo"]),
        license=str(data["license"]),
        test_paths=tuple(data["test_paths"]),
        include=bool(data["include"]),
        why=str(data["why"]),
        published_pin=dict(pin) if isinstance(pin, dict) else None,
        prior_power=dict(data["prior_power"]) if isinstance(data.get("prior_power"), dict) else None,
        raw=data,
    )


def validate_raw(raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if raw.get("schema_version") != 1:
        errors.append(f"schema_version must be 1, got {raw.get('schema_version')!r}")
    waves = raw.get("waves") or {}
    sources = raw.get("sources") or []
    ids: list[str] = []
    remotes: list[str] = []
    for data in sources:
        try:
            src = _as_source(data)
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(str(exc))
            continue
        ids.append(src.id)
        remotes.append(src.remote)
        if src.wave not in waves:
            errors.append(f"{src.id}: wave {src.wave!r} is not in waves")
        if src.wave == "wave0-published-fp":
            expected = WAVE0_REMOTES.get(src.id)
            if expected is None:
                errors.append(f"{src.id}: wave0 id is not one of {sorted(WAVE0_REMOTES)}")
            elif src.remote != expected:
                errors.append(
                    f"{src.id}: remote {src.remote!r} != greenwash bench remote {expected!r}"
                )
            if not src.published_pin:
                errors.append(f"{src.id}: wave0 requires published_pin")
    if len(ids) != len(set(ids)):
        errors.append("duplicate source id")
    if len(remotes) != len(set(remotes)):
        errors.append("duplicate remote")
    probes = raw.get("power_probes") or {}
    for key in ("patch", "unittest_assert", "approx", "skip", "js_test_globs"):
        if key not in probes:
            errors.append(f"power_probes missing {key}")
    return errors


def load_catalog(root: Path | None = None) -> Catalog:
    root = root or repo_root()
    raw = load(catalog_path(root))
    errors = validate_raw(raw)
    if errors:
        raise ValueError("catalog invalid:\n" + "\n".join(f"  - {e}" for e in errors))
    waves = {wid: _as_wave(wid, data) for wid, data in raw["waves"].items()}
    sources = [_as_source(data) for data in raw["sources"]]
    return Catalog(
        schema_version=int(raw["schema_version"]),
        engine_repo=str(raw["engine_repo"]),
        purpose=str(raw["purpose"]),
        waves=waves,
        sources=sources,
        power_probes=dict(raw["power_probes"]),
        raw=raw,
    )


def iter_included(catalog: Catalog) -> Iterator[Source]:
    yield from (s for s in catalog.sources if s.include)
