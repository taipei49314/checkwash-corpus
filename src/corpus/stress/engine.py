"""The judge, pinned to a release zipapp.

`analyze()` is imported *from the pyz* (zipimport), so the fast in-process
path runs the same bytes the release ships — the corpus README's lesson from
the 0.1.49 → 0.2.1 version drift. Every recorded finding is additionally
re-run through the zipapp's CLI on a real two-commit git repository: the path
a user actually runs, not the path the harness finds convenient.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

TODAY = datetime.date(2026, 1, 1)


@dataclass
class Judgement:
    verdict: str  # pass | block | error
    rules: list[str] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    seconds: float = 0.0
    error: str | None = None

    def canonical(self) -> str:
        rows = sorted(
            (
                f.get("rule"), f.get("severity"), f.get("path"), f.get("unit"),
                f.get("fingerprint"), tuple(f.get("escalators") or ()),
                tuple(f.get("deescalators") or ()),
            )
            for f in self.findings
        )
        return json.dumps([self.verdict, rows], sort_keys=True, default=str)


class Engine:
    def __init__(self, pyz: Path):
        self.pyz = pyz.resolve()
        if self.pyz.suffix.lower() != ".pyz":
            raise RuntimeError(f"engine must be a release zipapp, got {self.pyz}")
        self.sha256 = hashlib.sha256(self.pyz.read_bytes()).hexdigest()
        if "checkwash" in sys.modules:
            raise RuntimeError("checkwash was imported before the pyz was pinned; refuse to mix engines")
        sys.path.insert(0, str(self.pyz))
        import checkwash  # noqa: E402
        from checkwash.config import Config  # noqa: E402
        from checkwash.contract import Contract  # noqa: E402
        from checkwash.engine import FileChange, analyze  # noqa: E402
        from checkwash.pyenv import known_baseline  # noqa: E402

        origin = str(getattr(checkwash, "__file__", ""))
        if not origin.startswith(str(self.pyz)):
            raise RuntimeError(f"checkwash resolved to {origin}, not the pinned zipapp {self.pyz}")
        self.version = getattr(checkwash, "__version__", "?")
        self._Config, self._Contract, self._FileChange, self._analyze = Config, Contract, FileChange, analyze
        self._baseline = known_baseline()

    def record(self) -> dict:
        return {"asset": self.pyz.name, "sha256": self.sha256, "version": self.version}

    def judge(
        self,
        changes: list[tuple[str, bytes | None, bytes | None]],
        head: dict[str, bytes],
        modules: set[str],
        *,
        reverse: bool = False,
    ) -> Judgement:
        fcs = []
        for path, before, after in (reversed(changes) if reverse else changes):
            status = "modified" if before is not None and after is not None else ("added" if after is not None else "deleted")
            fcs.append(self._FileChange(path=path, status=status, before=before, after=after))
        started = time.perf_counter()
        try:
            _ir, findings, verdict = self._analyze(
                fcs, self._Config(), self._Contract(), [], TODAY,
                known_modules=self._baseline | set(modules),
                head_reader=head.get,
                head_searcher=lambda needles: [
                    p for p, d in sorted(head.items()) if any(n.encode("utf-8") in d for n in needles)
                ],
            )
        except BaseException as exc:  # noqa: BLE001 - a crash is the finding
            if isinstance(exc, KeyboardInterrupt):
                raise
            return Judgement(
                verdict="error",
                seconds=time.perf_counter() - started,
                error="".join(traceback.format_exception_only(type(exc), exc)).strip()
                + "\n"
                + "".join(traceback.format_tb(exc.__traceback__)[-3:]),
            )
        seconds = time.perf_counter() - started
        visible = [f for f in findings if not getattr(f, "allowlisted", False)]
        rows = []
        for f in visible:
            rows.append(
                {
                    "rule": f.rule,
                    "severity": f.severity,
                    "path": f.path,
                    "unit": f.unit,
                    "fingerprint": f.fingerprint,
                    "escalators": list(f.escalators),
                    "deescalators": list(f.deescalators),
                    "message": getattr(f, "message", ""),
                }
            )
        return Judgement(
            verdict=str(verdict),
            rules=sorted({f"{r['rule']}/{r['severity']}" for r in rows}),
            findings=rows,
            seconds=seconds,
        )

    def judge_twice(self, changes, head, modules) -> tuple[Judgement, bool]:
        first = self.judge(changes, head, modules)
        second = self.judge(changes, head, modules, reverse=True)
        return first, first.canonical() == second.canonical()


def _git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
        }
    )
    return env


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=stress", "-c", "user.email=stress@local",
         "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", *args],
        cwd=str(root), env=_git_env(), check=True, capture_output=True,
    )


def _write(root: Path, files: dict[str, bytes | None]) -> None:
    for path, data in files.items():
        target = root / path
        if data is None:
            if target.exists():
                target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def blackbox_check(
    pyz: Path,
    root: Path,
    before: dict[str, bytes],
    after: dict[str, bytes | None],
    python: str | None = None,
    timeout: int = 120,
) -> tuple[str | None, str]:
    """(verdict, note) from `python checkwash.pyz check HEAD~1..HEAD --format json`
    on a fresh repository holding `before` then `after`."""
    try:
        root.mkdir(parents=True, exist_ok=True)
        _git(root, "init", "-q")
        _write(root, before)
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "before")
        _write(root, after)
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "after")
    except (subprocess.CalledProcessError, OSError) as exc:
        return None, f"git setup failed: {exc}"
    argv = [python or sys.executable, str(pyz), "check", "HEAD~1..HEAD", "--format", "json"]
    try:
        proc = subprocess.run(argv, capture_output=True, cwd=str(root), timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "cli timeout"
    if proc.returncode not in (0, 1, 2):
        return "error", f"cli exit {proc.returncode}: {proc.stderr.decode('utf-8', 'replace')[-300:]}"
    try:
        payload = json.loads(proc.stdout.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
    verdict = payload.get("verdict") if isinstance(payload, dict) else None
    if verdict is None:
        verdict = {0: "pass", 1: "block", 2: "error"}[proc.returncode]
    return str(verdict), f"cli exit {proc.returncode}"
