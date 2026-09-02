"""What a run leaves behind: summary.json, REPORT.md, and one reproducer
directory per finding family — the minimised diff, a .gwcase skeleton, and
the exact command that reproduces it. Families, not floods: one hole is one
row however many mutants fell through it.
"""

from __future__ import annotations

import datetime
import json
import re
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

CLASS_DIRS = {
    "ESCAPE": "escapes",
    "FALSE_POSITIVE": "false_positives",
    "CRASH": "crashes",
    "NONDET": "nondeterminism",
    "BAD_VERDICT": "crashes",
    "NOOP_FINDINGS": "crashes",
}


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text)[:80].strip("-")


def write_repro(out_dir: Path, out, seed, changes, head: dict[str, bytes], judgement, before_files, after_files, engine_record) -> Path | None:
    sub = CLASS_DIRS.get(out.klass)
    if sub is None:
        return None
    parent = out_dir / sub
    parent.mkdir(parents=True, exist_ok=True)
    n = len([p for p in parent.iterdir() if p.is_dir()]) + 1
    repro = parent / f"{n:03d}-{_slug(out.family or out.klass)}"
    repro.mkdir(parents=True, exist_ok=True)
    for label, files in (("before", before_files), ("after", after_files)):
        for path, data in files.items():
            if data is None:
                continue
            target = repro / label / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    (repro / "judgement.json").write_text(
        json.dumps({"verdict": judgement.verdict, "rules": judgement.rules, "seconds": judgement.seconds, "error": judgement.error, "findings": judgement.findings, "engine": engine_record}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    (repro / "outcome.json").write_text(json.dumps(asdict(out), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    # .gwcase skeleton: changed files only; production as head snapshot.
    lines = ["=== meta ===", "rule: TODO", f"note: corpus stress {out.klass} family={out.family}",
             f"note2: seed={seed.id} iteration={out.iteration} ops={out.ops}",
             f"note3: engine verdict={judgement.verdict} rules={judgement.rules} blackbox={out.blackbox}",
             f"origin: corpus stress {datetime.date.today().isoformat()}, engine {engine_record.get('version')}",
             "=== env ==="] + sorted(seed.modules if seed is not None else [])
    for path, data in sorted(head.items()):
        lines += [f"=== head: {path} ===", data.decode("utf-8", "replace").rstrip("\n")]
    for path, b, a in changes:
        if b is not None:
            lines += [f"=== before: {path} ===", b.decode("utf-8", "replace").rstrip("\n")]
        if a is not None:
            lines += [f"=== after: {path} ===", a.decode("utf-8", "replace").rstrip("\n")]
    if out.klass == "ESCAPE":
        expect = '[{"rule": "TODO_EXPECTED_BLOCKING_RULE", "severity": "high"}]'
    elif out.klass == "FALSE_POSITIVE":
        expect = "[]"
    else:
        expect = json.dumps([{"rule": f["rule"], "severity": f["severity"]} for f in judgement.findings])
    lines += ["=== expect ===", expect, ""]
    (repro / "case.gwcase").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    readme = [
        f"# {out.klass}: {out.family}",
        "",
        f"- seed: `{seed.id}`; iteration {out.iteration}; ops {out.ops}" + (f" (minimised from {out.minimized_from})" if out.minimized_from else ""),
        f"- engine (in-process, from the zipapp): verdict `{judgement.verdict}`, rules {judgement.rules}, {judgement.seconds:.3f}s",
        f"- CLI re-verification on a real two-commit repo: `{out.blackbox}`" + (" — **DIVERGENCE from in-process verdict**" if out.divergence else ""),
        f"- deterministic (two runs, reversed change order): {out.deterministic}",
        "",
        "Reproduce: `before/` and `after/` are full trees (production + tests + config). Run pytest in each",
        "(`PYTHONPATH=src python -m pytest -q -p no:cacheprovider`) to re-check the oracle, then",
        "`git init` a repo, commit `before/`, commit `after/`, and `python checkwash.pyz check HEAD~1..HEAD`.",
        "`case.gwcase` is a fixture skeleton: fill in `rule:` and `expect` with the intended verdict.",
        "",
    ]
    if judgement.error:
        readme += ["## engine error", "", "```", judgement.error, "```", ""]
    (repro / "README.md").write_text("\n".join(readme), encoding="utf-8", newline="\n")
    return repro


def summarise(runner, *, final: bool) -> dict:
    cfg = runner.cfg
    by_mode = {m: Counter(c) for m, c in runner.by_mode.items()}
    elapsed = time.time() - runner.started
    families = {}
    for fam, row in runner.families.items():
        families[fam] = dict(row)
    return {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "final": final,
        "engine": runner.engine.record(),
        "config": {
            "modes": list(cfg.modes), "workers": cfg.workers, "master_seed": cfg.master_seed,
            "budget_seconds": cfg.seconds, "perf_budget_s": cfg.perf_budget_s,
            "perf_budget_mega_s": cfg.perf_budget_mega_s, "honest_share": cfg.honest_share,
            "checkwash_root": str(cfg.checkwash_root), "python": cfg.python,
        },
        "seeds": getattr(runner, "seed_report", {}),
        "elapsed_seconds": round(elapsed, 1),
        "iterations": runner.iterations_done,
        "by_mode": {m: dict(c) for m, c in sorted(by_mode.items())},
        "families": families,
        "repro_dirs_per_class": dict(runner.repro_counts),
        "coverage": dict(sorted(runner.coverage.items())),
        "perf_suspects_under_load": len(runner.perf_suspects),
        "perf_confirmed_alone": getattr(runner, "perf_confirmed", None),
        "engine_seconds_total": round(runner.engine_seconds_total, 2),
    }


def write_summary(out_dir: Path, summary: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def one_line(summary: dict) -> str:
    fams = summary["families"]
    counts = Counter(row["klass"] for row in fams.values())
    return (
        f"{summary['iterations']} iterations in {summary['elapsed_seconds']/3600:.2f} h; families: "
        + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) if counts else
        f"{summary['iterations']} iterations in {summary['elapsed_seconds']/3600:.2f} h; no findings"
    )


def _mode_table(summary: dict) -> list[str]:
    rows = ["| mode | " + " | ".join(("generated", "verified", "ESCAPE", "FALSE_POSITIVE", "CRASH", "NONDET", "DISCARDED", "INAPPLICABLE", "NOOP", "OK")) + " |", "|---|" + "---:|" * 10]
    for mode, counts in summary["by_mode"].items():
        gen = sum(counts.values())
        verified = sum(v for k, v in counts.items() if k in ("ESCAPE", "FALSE_POSITIVE", "OK", "NONDET", "CRASH"))
        rows.append(f"| {mode} | {gen} | {verified} | " + " | ".join(str(counts.get(k, 0)) for k in ("ESCAPE", "FALSE_POSITIVE", "CRASH", "NONDET", "DISCARDED", "INAPPLICABLE", "NOOP", "OK")) + " |")
    return rows


def _family_table(summary: dict, klass: str, mode_prefix: str | None = None) -> list[str]:
    rows = []
    for fam, row in sorted(summary["families"].items(), key=lambda kv: (-kv[1]["count"], kv[0])):
        if row["klass"] != klass:
            continue
        if mode_prefix and not fam.startswith(mode_prefix):
            continue
        bb = row.get("blackbox")
        flag = " **DIVERGENCE**" if row.get("divergence") else ""
        rows.append(f"| `{fam}` | {row['count']} | {bb}{flag} | `{row.get('repro')}` |")
    if not rows:
        return ["_none_"]
    return ["| family | count | CLI re-check | repro |", "|---|---:|---|---|"] + rows


def _coverage_table(summary: dict, prefix: str) -> list[str]:
    rows = ["| operator / spelling | generated | applicable | verified | findings |", "|---|---:|---:|---:|---:|"]
    for key, row in summary["coverage"].items():
        if not key.startswith(prefix):
            continue
        rows.append(f"| `{key[len(prefix):]}` | {row['generated']} | {row['applicable']} | {row['verified']} | {row['findings']} |")
    return rows if len(rows) > 2 else ["_none_"]


def write_report(out_dir: Path, summary: dict, runner) -> None:
    cal = None
    cal_path = out_dir / "calibration.json"
    if cal_path.exists():
        try:
            cal = json.loads(cal_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cal = None
    fams = summary["families"]
    counts = Counter(row["klass"] for row in fams.values())
    seeds = summary.get("seeds", {})
    lines = [
        f"# checkwash stress run — {out_dir.name}" + ("" if summary["final"] else " (in progress)"),
        "",
        f"Engine: `{summary['engine'].get('asset')}` v{summary['engine'].get('version')} (sha256 `{str(summary['engine'].get('sha256'))[:16]}…`). "
        f"{summary['iterations']} iterations in {summary['elapsed_seconds']/3600:.2f} h, {summary['config']['workers']} workers, PRNG seed `{summary['config']['master_seed']}`, "
        f"modes {', '.join(summary['config']['modes'])}. Seeds: {seeds.get('usable', '?')}/{seeds.get('loaded', '?')} usable"
        + (f" (dropped: {', '.join(d['id'] for d in seeds.get('dropped', []))})" if seeds.get("dropped") else "") + ".",
        "",
        "## Calibration (must pass before any number below is believed)",
        "",
    ]
    if cal is None:
        lines.append("_no calibration.json — numbers below are UNTRUSTED_")
    else:
        for name, gate in cal["gates"].items():
            detail = ", ".join(f"{k}={v}" for k, v in gate.items() if k not in ("pass", "mismatches", "oracle_disagreements"))
            lines.append(f"- {'ok' if gate['pass'] else '**FAIL**'} `{name}`: {detail}")
        lines.append(f"- overall: **{'PASS' if cal.get('pass') else 'FAIL'}**")
    lines += [
        "",
        "## Headline",
        "",
        f"Finding families: " + (", ".join(f"{k} {v}" for k, v in sorted(counts.items())) if counts else "none") + ".",
        "A family is one hole (operator chain + spelling, plus the rules that fired for false positives); "
        "the count is how many verified mutants fell through it. Every family's first instance was re-run through "
        "the zipapp CLI on a real two-commit repository (`CLI re-check`); a divergence from the in-process verdict is itself a finding.",
        "",
        "## By mode",
        "",
        *_mode_table(summary),
        "",
        "`verified` = the mechanical oracle agreed (tamper/open: red→green on buggy production; honest: still red on buggy, green on correct). "
        "`DISCARDED` = the edit did not verify and was thrown away, not counted against the engine.",
        "",
        "## Rule-space arm (operators written against THREATMODEL's taxonomy)",
        "",
        "### Escapes — verified tampering the engine passed",
        "",
        *_family_table(summary, "ESCAPE", "rules:"),
        "",
        "### False positives — verified honest refactors the engine blocked",
        "",
        *_family_table(summary, "FALSE_POSITIVE", "rules:"),
        "",
        "## Open-ended arm (random AST edits, oracle-filtered)",
        "",
        "### Escapes",
        "",
        *_family_table(summary, "ESCAPE", "open:"),
        "",
        "## Robustness",
        "",
        "### Crashes / bad verdicts",
        "",
        *_family_table(summary, "CRASH"),
        *([] if "BAD_VERDICT" not in counts else ["", *_family_table(summary, "BAD_VERDICT")]),
        *([] if "NOOP_FINDINGS" not in counts else ["", *_family_table(summary, "NOOP_FINDINGS")]),
        "",
        "### Non-determinism (same input, reversed change order, different output)",
        "",
        *_family_table(summary, "NONDET"),
        "",
        "### Perf",
        "",
        f"Inputs over budget while measured under load: {summary['perf_suspects_under_load']}. "
        + ("Re-measured alone (median of three) after the workers drained: "
           + (json.dumps(summary["perf_confirmed_alone"]) if summary["perf_confirmed_alone"] else "none still over budget.")
           if summary.get("perf_confirmed_alone") is not None else "Not yet re-measured (run in progress)."),
        "",
        "## Coverage — rule-space tamper operators",
        "",
        *_coverage_table(summary, "rules/tamper/"),
        "",
        "## Coverage — rule-space honest operators",
        "",
        *_coverage_table(summary, "rules/honest/"),
        "",
        "## Coverage — open-ended edits",
        "",
        *_coverage_table(summary, "open/open/"),
        "",
        "## Coverage — robustness inputs",
        "",
        *_coverage_table(summary, "robust/robust/"),
        "",
        "## Limits, stated",
        "",
        "- Only pytest-runnable configuration is generated (pytest.ini, conftest.py). CI workflow and Makefile weakenings have no mechanical oracle in this harness and are not measured here.",
        "- Seeds are the three shipped corpora: small single-function production. Larger shapes (fixtures, classes, cross-file helpers) are under-represented.",
        "- Every seed carries a two-test padding file so a neutralised test does not empty the run; that is the realistic suite shape, and it is identical on both sides.",
        "- `async_convert` (an orphan `async def` test with no async plugin) is pytest-version-dependent: some versions skip it (green — a wash), others fail it. The oracle decides per run; a verified escape here means *this* pytest skipped it.",
        "- Open-ended edits explore only the palette in `random_ops.py`; a family the palette cannot express is not in this report.",
        "- Findings are candidates: `case.gwcase` skeletons carry `rule: TODO` and are not committed by the harness (AGENTS.md rule 2 — labels are reviewed by a human).",
        "",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
