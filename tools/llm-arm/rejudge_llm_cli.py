#!/usr/bin/env python3
"""Re-judge a recorded stress LLM-arm record through the zipapp's CLI path.

For every family directory under ``<record>/escapes`` and ``<record>/false_positives`` this
materialises ``before/`` then ``after/`` as the two commits of a fresh git repository exactly
as ``corpus.stress.engine.blackbox_check`` does (the same ``_git`` / ``_write`` helpers, the
same ``python <pyz> check HEAD~1..HEAD --format json`` command, the same exit-code fallback)
and records the verdict and the findings the CLI prints. Nothing is judged in-process: the
harness's in-process judge lacks the strict-snapshot wiring checkwash's own adapters use
since 0.3.0 (corpus issue #15), so only the CLI path is the user path.

Outputs, under ``--out``:

  results.json   ``meta`` (record, pyz sha256 and size, python, host, corpus commit, timing),
                 ``families`` (one entry per family: what the record says, what the CLI says
                 now, findings, highest severity, seconds) and ``summary`` (recorded-CLI ->
                 now-CLI verdict matrix per class, highest-severity histogram, flips, errors)
  SUMMARY.md     the same summary as Markdown tables
  cli/<class>/<family>.json   the raw CLI stdout per family (or the raw text when not JSON)

``--limit N`` keeps the first N families of each class (a trial run); ``0`` means all.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import platform
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CLASSES = (("ESCAPE", "escapes"), ("FALSE_POSITIVE", "false_positives"))
SEVERITY_RANK = {"critical": 4, "high": 3, "warn": 2, "info": 1}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tree(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = Path(dirpath) / name
            files[full.relative_to(root).as_posix()] = full.read_bytes()
    return files


def rmtree(path: Path) -> None:
    def onerror(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    shutil.rmtree(path, onerror=onerror)


def highest_severity(findings: list[dict]) -> str:
    best = "none"
    rank = 0
    for f in findings:
        sev = str(f.get("severity", "")).lower()
        if SEVERITY_RANK.get(sev, 0) > rank:
            rank, best = SEVERITY_RANK[sev], sev
    return best


def load_json_if(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def family_dirs(record: Path, limit: int) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for klass, sub in CLASSES:
        base = record / sub
        if not base.is_dir():
            continue
        dirs = sorted(p for p in base.iterdir() if p.is_dir() and (p / "before").is_dir() and (p / "after").is_dir())
        if limit > 0:
            dirs = dirs[:limit]
        out.extend((klass, d) for d in dirs)
    return out


def judge_one(python: str, pyz: Path, root: Path, before: dict[str, bytes], after: dict[str, bytes | None],
              timeout: int, git, write) -> dict:
    """The CLI path of corpus.stress.engine.blackbox_check, keeping the findings."""
    result: dict = {"verdict": None, "exit": None, "note": "", "findings": [], "stdout": "", "stderr": "", "seconds": None}
    try:
        root.mkdir(parents=True, exist_ok=True)
        git(root, "init", "-q")
        write(root, before)
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "before")
        write(root, after)
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "after")
    except (subprocess.CalledProcessError, OSError) as exc:
        result["note"] = f"git setup failed: {exc}"
        return result
    argv = [python, str(pyz), "check", "HEAD~1..HEAD", "--format", "json"]
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(argv, capture_output=True, cwd=str(root), timeout=timeout)
    except subprocess.TimeoutExpired:
        result["seconds"] = round(time.perf_counter() - t0, 3)
        result["note"] = "cli timeout"
        return result
    result["seconds"] = round(time.perf_counter() - t0, 3)
    result["exit"] = proc.returncode
    result["stdout"] = proc.stdout.decode("utf-8", "replace")
    result["stderr"] = proc.stderr.decode("utf-8", "replace")[-2000:]
    if proc.returncode not in (0, 1, 2):
        result["verdict"] = "error"
        result["note"] = f"cli exit {proc.returncode}: {result['stderr'][-300:]}"
        return result
    try:
        payload = json.loads(result["stdout"])
    except ValueError:
        payload = {}
    verdict = payload.get("verdict") if isinstance(payload, dict) else None
    if verdict is None:
        verdict = {0: "pass", 1: "block", 2: "error"}[proc.returncode]
    result["verdict"] = str(verdict)
    result["note"] = f"cli exit {proc.returncode}"
    findings = payload.get("findings") if isinstance(payload, dict) else None
    if isinstance(findings, list):
        result["findings"] = [
            {k: f.get(k) for k in ("rule", "severity", "path", "unit", "message", "fingerprint", "escalators", "deescalators")}
            for f in findings if isinstance(f, dict)
        ]
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--record", required=True, help="records/stress/<run> directory")
    ap.add_argument("--pyz", required=True, help="the release zipapp to judge with")
    ap.add_argument("--out", required=True, help="output directory (created)")
    ap.add_argument("--limit", type=int, default=0, help="first N families per class; 0 = all")
    ap.add_argument("--python", default=sys.executable, help="interpreter that runs the zipapp")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per CLI call")
    ap.add_argument("--corpus-src", default=None, help="corpus src dir (default: ../../src relative to this file)")
    ap.add_argument("--scratch", default=None, help="where the two-commit repositories are built (default: a temp dir)")
    args = ap.parse_args()

    corpus_src = Path(args.corpus_src) if args.corpus_src else Path(__file__).resolve().parents[2] / "src"
    sys.path.insert(0, str(corpus_src))
    from corpus.stress.engine import _git, _write  # the helpers blackbox_check uses

    record = Path(args.record).resolve()
    pyz = Path(args.pyz).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "cli").mkdir(exist_ok=True)
    scratch = Path(args.scratch).resolve() if args.scratch else Path(tempfile.mkdtemp(prefix="llm-rejudge-"))
    scratch.mkdir(parents=True, exist_ok=True)

    record_summary = load_json_if(record / "summary.json") or {}
    record_calibration = load_json_if(record / "calibration.json") or {}
    try:
        corpus_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(corpus_src.parent), capture_output=True,
                                       text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        corpus_commit = None
    try:
        py_version = subprocess.run([args.python, "-c", "import platform,sys;print(platform.python_version(), sys.executable)"],
                                    capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        py_version = f"unknown ({exc})"

    started = datetime.datetime.now(datetime.timezone.utc)
    families = family_dirs(record, args.limit)
    rows: list[dict] = []
    for i, (klass, fam) in enumerate(families, 1):
        outcome = load_json_if(fam / "outcome.json") or {}
        before = read_tree(fam / "before")
        after_tree = read_tree(fam / "after")
        after: dict[str, bytes | None] = dict(after_tree)
        for p in before:
            if p not in after_tree:
                after[p] = None
        root = scratch / f"{klass.lower()}-{i:03d}"
        if root.exists():
            rmtree(root)
        judged = judge_one(args.python, pyz, root, before, after, args.timeout, _git, _write)
        try:
            rmtree(root)
        except OSError:
            pass
        raw_dir = out / "cli" / klass.lower()
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / f"{fam.name}.json"
        try:
            raw_path.write_text(json.dumps(json.loads(judged["stdout"]), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        except ValueError:
            raw_path.with_suffix(".txt").write_text(judged["stdout"] + "\n--- stderr ---\n" + judged["stderr"], encoding="utf-8")
        recorded_blackbox = outcome.get("blackbox")
        recorded_inprocess = outcome.get("verdict")
        now = judged["verdict"]
        row = {
            "class": klass,
            "dir": f"{'escapes' if klass == 'ESCAPE' else 'false_positives'}/{fam.name}",
            "family": outcome.get("family"),
            "seed_id": outcome.get("seed_id"),
            "iteration": outcome.get("iteration"),
            "kind": outcome.get("kind"),
            "recorded": {
                "inprocess_verdict": recorded_inprocess,
                "inprocess_rules": outcome.get("rules"),
                "cli_verdict": recorded_blackbox,
                "divergence": outcome.get("divergence"),
            },
            "now": {
                "cli_verdict": now,
                "exit": judged["exit"],
                "note": judged["note"],
                "rules": sorted({f"{f.get('rule')}/{f.get('severity')}" for f in judged["findings"] if f.get("rule")}),
                "highest_severity": highest_severity(judged["findings"]),
                "findings": judged["findings"],
                "seconds": judged["seconds"],
            },
            "flipped_vs_recorded_cli": (recorded_blackbox is not None and now is not None and now != recorded_blackbox),
            "differs_from_recorded_inprocess": (recorded_inprocess is not None and now is not None and now != recorded_inprocess),
            "files_before": len(before),
            "files_after": len(after_tree),
        }
        rows.append(row)
        sys.stdout.write(f"[{i}/{len(families)}] {klass} {fam.name[:60]} recorded_cli={recorded_blackbox} now={now} "
                         f"sev={row['now']['highest_severity']} {judged['seconds']}s\n")
        sys.stdout.flush()
    finished = datetime.datetime.now(datetime.timezone.utc)

    # ---- summary -----------------------------------------------------------------------------
    def matrix(klass: str) -> dict[str, int]:
        m: dict[str, int] = {}
        for r in rows:
            if r["class"] != klass:
                continue
            key = f"{r['recorded']['cli_verdict']}->{r['now']['cli_verdict']}"
            m[key] = m.get(key, 0) + 1
        return dict(sorted(m.items()))

    def severity_hist(klass: str, now_verdict: str) -> dict[str, int]:
        h = {k: 0 for k in ("critical", "high", "warn", "info", "none")}
        for r in rows:
            if r["class"] == klass and r["now"]["cli_verdict"] == now_verdict:
                h[r["now"]["highest_severity"]] = h.get(r["now"]["highest_severity"], 0) + 1
        return h

    flips = [
        {"class": r["class"], "dir": r["dir"], "family": r["family"], "recorded_cli": r["recorded"]["cli_verdict"],
         "now": r["now"]["cli_verdict"], "rules_now": r["now"]["rules"]}
        for r in rows if r["flipped_vs_recorded_cli"]
    ]
    errors = [{"class": r["class"], "dir": r["dir"], "note": r["now"]["note"]} for r in rows
              if r["now"]["cli_verdict"] in (None, "error")]
    seconds = [r["now"]["seconds"] for r in rows if r["now"]["seconds"] is not None]
    summary = {
        "families_judged": len(rows),
        "by_class": {klass: sum(1 for r in rows if r["class"] == klass) for klass, _ in CLASSES},
        "recorded_cli_to_now_cli": {klass: matrix(klass) for klass, _ in CLASSES},
        "escape_still_pass_highest_severity": severity_hist("ESCAPE", "pass"),
        "escape_now_block_highest_severity": severity_hist("ESCAPE", "block"),
        "false_positive_still_block_highest_severity": severity_hist("FALSE_POSITIVE", "block"),
        "false_positive_now_pass_highest_severity": severity_hist("FALSE_POSITIVE", "pass"),
        "flips_vs_recorded_cli": flips,
        "errors_or_timeouts": errors,
        "seconds": {"total": round(sum(seconds), 1), "mean": round(sum(seconds) / len(seconds), 2) if seconds else None,
                    "max": max(seconds) if seconds else None},
    }
    meta = {
        "schema_version": 1,
        "kind": "llm-arm-rejudge-cli",
        "record": str(record),
        "record_engine": record_summary.get("engine") or record_calibration.get("engine"),
        "record_generated": record_summary.get("generated"),
        "record_iterations": record_summary.get("iterations"),
        "pyz": str(pyz),
        "pyz_sha256": sha256_of(pyz),
        "pyz_bytes": pyz.stat().st_size,
        "python": py_version,
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "corpus_src": str(corpus_src),
        "corpus_commit": corpus_commit,
        "limit": args.limit,
        "timeout_seconds": args.timeout,
        "command": "python <pyz> check HEAD~1..HEAD --format json on a fresh two-commit repository per family (corpus.stress.engine.blackbox_check materialisation)",
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": finished.isoformat(timespec="seconds"),
        "elapsed_seconds": round((finished - started).total_seconds(), 1),
    }
    (out / "results.json").write_text(json.dumps({"meta": meta, "summary": summary, "families": rows}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    lines: list[str] = []
    w = lines.append
    w(f"# LLM-arm re-judge through the CLI path: {record.name}")
    w("")
    w(f"- record: `{record.name}` (engine {json.dumps(meta['record_engine'])}, generated {meta['record_generated']}, {meta['record_iterations']} iterations)")
    w(f"- engine now: `{pyz.name}` sha256 `{meta['pyz_sha256']}` ({meta['pyz_bytes']} bytes)")
    w(f"- python: {meta['python']}; host: {meta['host']}; corpus commit: {meta['corpus_commit']}")
    w(f"- families judged: {summary['families_judged']} ({summary['by_class']}); limit {args.limit}; "
      f"{meta['elapsed_seconds']} s total, mean {summary['seconds']['mean']} s per family, max {summary['seconds']['max']} s")
    w(f"- command per family: `{meta['command']}`")
    w("")
    w("## Recorded CLI verdict -> CLI verdict now")
    w("")
    w("| class | recorded -> now | families |")
    w("|---|---|---:|")
    for klass, _ in CLASSES:
        for key, n in summary["recorded_cli_to_now_cli"][klass].items():
            w(f"| {klass} | {key} | {n} |")
    w("")
    w("## Highest finding severity per family (CLI now)")
    w("")
    w("| population | critical | high | warn | info | no finding |")
    w("|---|---:|---:|---:|---:|---:|")
    for label, key in (("escapes that still pass", "escape_still_pass_highest_severity"),
                       ("escapes that now block", "escape_now_block_highest_severity"),
                       ("false positives that still block", "false_positive_still_block_highest_severity"),
                       ("false positives that now pass", "false_positive_now_pass_highest_severity")):
        h = summary[key]
        w(f"| {label} | {h['critical']} | {h['high']} | {h['warn']} | {h['info']} | {h['none']} |")
    w("")
    w(f"## Flips versus the recorded CLI verdict ({len(flips)})")
    w("")
    w("| class | repro | recorded | now | rules now |")
    w("|---|---|---|---|---|")
    for f in flips:
        w(f"| {f['class']} | `{f['dir']}` | {f['recorded_cli']} | {f['now']} | {', '.join(f['rules_now']) or '—'} |")
    w("")
    w(f"## Errors or timeouts ({len(errors)})")
    w("")
    for e in errors:
        w(f"- {e['class']} `{e['dir']}`: {e['note']}")
    if not errors:
        w("- none")
    w("")
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.write("\n".join(lines[:12]) + "\n")
    if not args.scratch:
        try:
            rmtree(scratch)
        except OSError:
            pass
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
