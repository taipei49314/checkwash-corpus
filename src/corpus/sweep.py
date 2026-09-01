from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from corpus.catalog import Catalog, Source
from corpus.engine import EngineError, resolve_engine
from corpus.gitutil import has_commit
from corpus.jsonio import dump
from corpus.paths import inspect_clone, resolve_clone, sweep_path


class SweepError(RuntimeError):
    pass


def run_sweep(
    root: Path,
    catalog: Catalog,
    source: Source,
    *,
    engine: str | None,
    replace: bool = False,
    allow_dirty: bool = False,
) -> Path:
    repo = resolve_clone(root, source.id)
    if repo is None:
        state, path = inspect_clone(root, source.id)
        if state == "broken":
            raise SweepError(
                f"{source.id}: {path} is a broken leftover, not a clone"
            )
        raise SweepError(f"{source.id}: clone missing at {path}")
    wave = catalog.waves[source.wave]
    dest = sweep_path(root, source.id)
    if dest.exists() and not replace:
        raise SweepError(
            f"{dest} already exists; pass --replace to overwrite a recorded sweep"
        )
    pin = (source.published_pin or {}).get("newest_commit")
    if pin and not has_commit(repo, pin):
        raise SweepError(f"{source.id}: clone does not contain pin {pin}")
    try:
        cmd, engine_record = resolve_engine(engine, allow_dirty=allow_dirty)
    except EngineError as exc:
        raise SweepError(str(exc)) from exc
    env = os.environ.copy()
    if engine and Path(engine).is_dir():
        src = Path(engine) / "src"
        if src.is_dir():
            env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
            if cmd[-1] in {"checkwash", "greenwash"} and cmd[0] == sys.executable:
                pass
    rev = pin or "HEAD"
    argv = cmd + ["sweep", rev, "--limit", str(wave.commit_limit), "--repo", str(repo)]
    proc = subprocess.run(argv, capture_output=True, env=env)
    if proc.returncode not in (0, 1):
        err = proc.stderr.decode("utf-8", "replace").strip()
        raise SweepError(
            f"{source.id}: engine exited {proc.returncode}: {err or proc.stdout[:500]!r}"
        )
    try:
        payload = json.loads(proc.stdout.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SweepError(f"{source.id}: engine stdout is not JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SweepError(f"{source.id}: engine JSON is not an object")
    payload["catalog_id"] = source.id
    payload["wave"] = source.wave
    payload["engine"] = engine_record
    corpus = payload.get("corpus")
    if not isinstance(corpus, dict) or not corpus.get("newest_commit") or not corpus.get("oldest_commit"):
        raise SweepError(f"{source.id}: engine JSON missing corpus pins")
    dump(dest, payload)
    return dest
