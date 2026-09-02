"""Materialise a seed variant on disk and ask pytest whether CI would be green.

The invocation mirrors benchmarks/tamper/verify.py and
benchmarks/refactors/verify.py in the checkwash checkout — same flags, same
hermetic environment — so a verdict the harness records is one those
harnesses would also have recorded. "Green" means exit code 0: the CI
definition. Skipped, xfailed, deselected-but-others-remain and collect-only
runs are all green, which is exactly the attack surface.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path


def materialise(root: Path, prod: dict[str, bytes], tests: dict[str, str | bytes | None], extras: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for path, data in prod.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for path, text in tests.items():
        if text is None:
            continue
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            target.write_bytes(text)
        else:
            target.write_text(text, encoding="utf-8", newline="\n")
    for path, text in extras.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")


def _on_rm_error(func, path, _exc):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        pass


def remove_tree(path: Path) -> None:
    for _ in range(3):
        try:
            shutil.rmtree(path, onerror=_on_rm_error)
            return
        except OSError:
            continue


class Workspace:
    """A fresh directory per mutant under the gitignored clones cache."""

    def __init__(self, base: Path, label: str = "mut"):
        self.base = base
        self.path = base / f"{label}-{uuid.uuid4().hex[:12]}"

    def __enter__(self) -> Path:
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    def __exit__(self, *exc) -> None:
        remove_tree(self.path)


def pytest_env(src_dir: Path) -> dict[str, str]:
    env = {
        "PATH": "",
        "PYTHONPATH": str(src_dir),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
    }
    for key in ("TEMP", "TMP", "HOME", "USERPROFILE", "LOCALAPPDATA"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def ci_green(root: Path, python: str | None = None, timeout: int = 60) -> str:
    """'green' | 'red' | 'timeout' | 'error'. Bare `pytest` so pytest.ini
    (testpaths, addopts) decides what runs, as it would in CI."""
    argv = [python or sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            cwd=str(root),
            env=pytest_env(root / "src"),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "timeout"
    except OSError:
        return "error"
    return "green" if proc.returncode == 0 else "red"
