"""Identify the checkwash/greenwash binary a sweep will run.

Published records must name a Release zipapp (`checkwash.pyz` now,
`greenwash.pyz` on tags ≤v0.1.49) and its sha256. PATH / editable
checkouts are dirty: they wrote the 0.1.49→0.2.1 version drift.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PYZ_ASSETS = frozenset({"checkwash.pyz", "greenwash.pyz"})


class EngineError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_engine(explicit: str | None, *, allow_dirty: bool) -> tuple[list[str], dict]:
    """Return (argv, engine record). Record has no machine-local paths."""
    if explicit:
        path = Path(explicit)
        if path.is_dir():
            return _dirty(allow_dirty, "editable", _checkout_cmd(path))
        if path.is_file():
            if path.suffix.lower() == ".pyz":
                name = path.name.lower()
                if name not in PYZ_ASSETS:
                    raise EngineError(
                        f"{path.name} is a zipapp but not a known release asset "
                        f"(want checkwash.pyz, or greenwash.pyz for ≤v0.1.49)"
                    )
                return [sys.executable, str(path.resolve())], {
                    "asset": name,
                    "sha256": sha256_file(path),
                }
            exe = path.resolve()
            return _dirty(allow_dirty, "path-executable", [str(exe)])
        found = shutil.which(explicit)
        if found:
            return _dirty(allow_dirty, "path-executable", [found])
        raise EngineError(f"engine not found: {explicit}")

    for name in ("checkwash", "greenwash"):
        found = shutil.which(name)
        if found:
            return _dirty(allow_dirty, "path-executable", [found])
    raise EngineError(
        "no engine given and none on PATH. Pass --engine checkwash.pyz "
        "(current Release asset). greenwash.pyz is ≤v0.1.49 only."
    )


def _checkout_cmd(path: Path) -> list[str]:
    src = path / "src"
    if (src / "checkwash").is_dir():
        return [sys.executable, "-m", "checkwash"]
    if (src / "greenwash").is_dir():
        return [sys.executable, "-m", "greenwash"]
    return [sys.executable, "-m", "checkwash"]


def _dirty(allow: bool, asset: str, argv: list[str]) -> tuple[list[str], dict]:
    if not allow:
        raise EngineError(
            "refusing a dirty engine (PATH, checkout, or non-pyz file). "
            "Pass --engine checkwash.pyz, or --allow-dirty-engine for a local "
            "experiment that validate will reject on wave 1."
        )
    return argv, {"asset": asset, "sha256": None}
