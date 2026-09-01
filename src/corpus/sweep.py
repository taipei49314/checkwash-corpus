from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from corpus.catalog import Catalog, Source
from corpus.gitutil import GitError, has_commit, is_git_repo
from corpus.jsonio import dump
from corpus.paths import clone_path, sweep_path


class SweepError(RuntimeError):
    pass


def find_engine(explicit: str | None) -> list[str]:
    if explicit:
        path = Path(explicit)
        if path.is_dir():
            return [sys.executable, "-m", "checkwash"]
        if path.is_file():
            return [sys.executable, str(path)]
        exe = shutil.which(explicit)
        if exe:
            return [exe]
        raise SweepError(f"engine not found: {explicit}")
    for name in ("greenwash", "checkwash"):
        exe = shutil.which(name)
        if exe:
            return [exe]
    raise SweepError(
        "no greenwash/checkwash on PATH; pass --engine PATH "
        "(a checkout, a pyz, or an executable)"
    )


def run_sweep(
    root: Path,
    catalog: Catalog,
    source: Source,
    *,
    engine: str | None,
    replace: bool = False,
) -> Path:
    repo = clone_path(root, source.id)
    if not is_git_repo(repo):
        raise SweepError(f"{source.id}: clone missing at {repo}")
    wave = catalog.waves[source.wave]
    dest = sweep_path(root, source.id)
    if dest.exists() and not replace:
        raise SweepError(
            f"{dest} already exists; pass --replace to overwrite a recorded sweep"
        )
    pin = (source.published_pin or {}).get("newest_commit")
    if pin and not has_commit(repo, pin):
        raise SweepError(f"{source.id}: clone does not contain pin {pin}")
    cmd = find_engine(engine)
    # If --engine is a checkout, run with PYTHONPATH=src so -m checkwash / greenwash resolves.
    env = os.environ.copy()
    if engine and Path(engine).is_dir():
        src = Path(engine) / "src"
        if src.is_dir():
            env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
            # Prefer the package that actually exists in that checkout.
            if (src / "checkwash").is_dir():
                cmd = [sys.executable, "-m", "checkwash"]
            elif (src / "greenwash").is_dir():
                cmd = [sys.executable, "-m", "greenwash"]
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
    corpus = payload.get("corpus")
    if not isinstance(corpus, dict) or not corpus.get("newest_commit") or not corpus.get("oldest_commit"):
        raise SweepError(f"{source.id}: engine JSON missing corpus pins")
    dump(dest, payload)
    return dest
