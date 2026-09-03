"""corpus CLI — fetch, census, harvest, sweep, status, validate.

Exit 0 success; 1 a catalogued unit failed; 2 tool/input error. SPEC §10.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from corpus import __version__
from corpus.catalog import load_catalog
from corpus.paths import repo_root


def _today() -> str:
    return datetime.date.today().isoformat()


def _load(args: argparse.Namespace):
    root = Path(args.root).resolve() if args.root else repo_root()
    try:
        catalog = load_catalog(root)
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc
    return root, catalog


def _select(catalog, args):
    try:
        return catalog.select(
            wave=args.wave,
            source_id=args.id,
            include_planned=getattr(args, "include_planned", False),
        )
    except (KeyError, ValueError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc


def cmd_status(args: argparse.Namespace) -> int:
    from corpus.status import field_run_status, source_status, wave_status

    root, catalog = _load(args)
    waves = wave_status(root, catalog)
    for wave_id, row in waves.items():
        planned = row["catalogued"] - row["included"]
        extra = f", {planned} planned" if planned else ""
        broken = f"; {row['broken']} broken" if row.get("broken") else ""
        print(
            f"{wave_id:24} {row['included']}/{row['catalogued']} catalogued{extra}; "
            f"{row['cloned']} cloned{broken}; {row['census']} census; "
            f"{row['sweeps']} sweeps; {row['prs']} harvested PRs"
        )
    for run in field_run_status(root):
        print(
            f"{run['id']:24} field-run {run['sweeps']} sweeps, "
            f"{run['adjudicated']} adjudicated; "
            f"{run['commits_blocked']}/{run['commits_analysed']} blocked"
        )
    if args.verbose:
        print()
        for src in catalog.sources:
            st = source_status(root, catalog, src.id)
            flag = " " if st["include"] else "*"
            print(
                f"  {flag}{st['id']:22} clone={st['clone_state']:7} "
                f"pin={int(st['pin_present'])} census={int(st['census'])} "
                f"sweep={int(st['sweep'])} prs={st['prs']}"
            )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from corpus.validate import validate

    root = Path(args.root).resolve() if args.root else repo_root()
    errors = validate(root)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("catalog and records: ok")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    from corpus.fetch import fetch_many

    root, catalog = _load(args)
    sources = _select(catalog, args)
    if not sources:
        print("nothing to fetch (empty selection)", file=sys.stderr)
        return 2

    def progress(sid: str, msg: str | None, err: str | None) -> None:
        if err:
            print(f"FAIL {sid}: {err}", file=sys.stderr)
        else:
            print(msg)

    results = fetch_many(
        root, catalog, sources, layout=args.layout, on_progress=progress
    )
    failed = [sid for sid, err in results if err]
    if failed:
        print(f"{len(failed)} source(s) failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def cmd_census(args: argparse.Namespace) -> int:
    from corpus.census import run_census
    from corpus.gitutil import GitError

    root, catalog = _load(args)
    sources = _select(catalog, args)
    if not sources:
        print("nothing to census", file=sys.stderr)
        return 2
    failed: list[str] = []
    for src in sources:
        try:
            dest = run_census(root, catalog, src)
            print(f"wrote {dest.relative_to(root)}")
        except GitError as exc:
            print(f"FAIL {src.id}: {exc}", file=sys.stderr)
            failed.append(src.id)
    if failed:
        print(f"{len(failed)} source(s) failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def cmd_harvest(args: argparse.Namespace) -> int:
    from corpus.harvest import HarvestError, harvest_source

    root, catalog = _load(args)
    sources = _select(catalog, args)
    if not sources:
        print("nothing to harvest", file=sys.stderr)
        return 2
    failed: list[str] = []
    day = _today()
    for src in sources:
        try:
            stats = harvest_source(root, src, per_repo=args.per_repo, harvested_on=day)
            print(
                f"{src.id}: scanned {stats['scanned']} PRs, "
                f"kept {stats['kept']}, already-had {stats['skipped_identity']}"
            )
        except HarvestError as exc:
            print(f"FAIL {src.id}: {exc}", file=sys.stderr)
            failed.append(src.id)
    if failed:
        print(f"{len(failed)} source(s) failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    from corpus.sweep import SweepError, run_sweep

    root, catalog = _load(args)
    sources = _select(catalog, args)
    if not sources:
        print("nothing to sweep", file=sys.stderr)
        return 2
    failed: list[str] = []
    for src in sources:
        try:
            dest = run_sweep(
                root,
                catalog,
                src,
                engine=args.engine,
                replace=args.replace,
                allow_dirty=args.allow_dirty_engine,
            )
            print(f"wrote {dest.relative_to(root)}")
        except SweepError as exc:
            print(f"FAIL {src.id}: {exc}", file=sys.stderr)
            failed.append(src.id)
    if failed:
        print(f"{len(failed)} source(s) failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="corpus",
        description="checkwash-corpus: fetch, census, harvest, sweep, validate",
    )
    p.add_argument("--root", default=None, help="corpus checkout (default: walk up)")
    p.add_argument("--version", action="version", version=f"checkwash-corpus {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    st = sub.add_parser("status", help="what is catalogued vs cloned vs recorded")
    st.add_argument("-v", "--verbose", action="store_true")
    st.set_defaults(func=cmd_status)

    va = sub.add_parser("validate", help="fail closed on catalog/record contract")
    va.set_defaults(func=cmd_validate)

    def add_select(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--wave", default=None)
        sp.add_argument("--id", default=None, help="single catalog id")
        sp.add_argument(
            "--include-planned",
            action="store_true",
            help="also operate on include=false sources",
        )

    fe = sub.add_parser("fetch", help="clone or update catalogued sources into clones/")
    add_select(fe)
    fe.add_argument(
        "--layout",
        choices=("cache", "bench"),
        default="cache",
        help="cache: clones/<id>. bench: wave0 at repo root so `greenwash bench --corpus .` works when this checkout is named greenwash-corpus",
    )
    fe.set_defaults(func=cmd_fetch)

    ce = sub.add_parser("census", help="count patch/unittest/JS/runner power at the pin")
    add_select(ce)
    ce.set_defaults(func=cmd_census)

    ha = sub.add_parser("harvest-prs", help="store merged PRs that touch test files")
    add_select(ha)
    ha.add_argument("--per-repo", type=int, default=15)
    ha.set_defaults(func=cmd_harvest)

    sw = sub.add_parser("sweep", help="run greenwash/checkwash sweep; record JSON")
    add_select(sw)
    sw.add_argument(
        "--engine",
        default=None,
        help="checkwash.pyz (current Release asset), a checkout, or an executable; greenwash.pyz is ≤v0.1.49 only",
    )
    sw.add_argument("--replace", action="store_true")
    sw.add_argument(
        "--allow-dirty-engine",
        action="store_true",
        help="allow PATH/checkout engines; wave1 records still fail validate",
    )
    sw.set_defaults(func=cmd_sweep)

    st_ = sub.add_parser("stress", help="24-hour mechanical falsification of checkwash's claims")
    st_sub = st_.add_subparsers(dest="stress_command", required=True)

    def add_stress_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--engine", required=True, help="checkwash.pyz (a Release asset; the judge is imported from it)")
        sp.add_argument("--checkwash", default=None, help="checkwash checkout holding benchmarks/ (default: sibling ../checkwash)")
        sp.add_argument("--out", default=None, help="output dir (default: records/stress/<date>)")
        sp.add_argument("--python", default=None, help="interpreter for the pytest oracle (default: this one)")
        sp.add_argument("--allow-stale-engine", action="store_true", help="measure an engine older than the checkwash checkout on purpose (refused by default)")

    sr = st_sub.add_parser("run", help="generate, verify, judge, record")
    add_stress_common(sr)
    sr.add_argument("--hours", type=float, default=None, help="0 = run until a STOP file appears in the output dir, or Ctrl-C")
    sr.add_argument("--minutes", type=float, default=None)
    sr.add_argument("--iterations", type=int, default=None)
    sr.add_argument("--workers", type=int, default=4)
    sr.add_argument("--seed", default=None, help="PRNG master seed (default: today's date)")
    sr.add_argument("--modes", default="rules,open,robust")
    sr.add_argument("--skip-calibration", action="store_true")
    # LLM arm (--modes llm): a local model proposes, the harness decides.
    sr.add_argument("--llm-url", default=None, help="model server (default http://127.0.0.1:11434; LM Studio server: http://127.0.0.1:1234)")
    sr.add_argument("--llm-model", default=None, help="model name (default qwen2.5-coder:7b)")
    sr.add_argument("--llm-api", default=None, choices=["auto", "ollama", "openai"], help="auto: Ollama native on :11434, OpenAI-compatible otherwise")
    sr.add_argument("--llm-temperature", type=float, default=None, help="default 0.9")
    sr.add_argument("--llm-num-ctx", type=int, default=None, help="context window to request (default 8192)")
    sr.add_argument("--llm-timeout", type=int, default=None, help="seconds per completion (default 600)")
    sr.add_argument("--llm-briefs", default=None, help="brief weights, e.g. attack=0.6,honest=0.25,config=0.15")
    sr.set_defaults(func=cmd_stress_run)

    sc = st_sub.add_parser("calibrate", help="replay the recorded corpora through the harness; must pass")
    add_stress_common(sc)
    sc.add_argument("--hours", type=float, default=None)
    sc.add_argument("--minutes", type=float, default=None)
    sc.add_argument("--iterations", type=int, default=None)
    sc.add_argument("--workers", type=int, default=1)
    sc.add_argument("--seed", default=None)
    sc.add_argument("--modes", default="rules,open,robust")
    sc.set_defaults(func=cmd_stress_calibrate)

    pr = sub.add_parser("probe", help="the natural arm: an agent really works a red repository; execution classifies, the pinned zipapp judges")
    pr_sub = pr.add_subparsers(dest="probe_command", required=True)

    pp = pr_sub.add_parser("prepare", help="one git repository per (seed, level), CI red at the baseline, the prompt beside it")
    pp.add_argument("--engine", required=True, help="checkwash.pyz the batch will be judged with (recorded; collect refuses another)")
    pp.add_argument("--checkwash", default=None, help="checkwash checkout holding benchmarks/ (default: sibling ../checkwash)")
    pp.add_argument("--out", required=True, help="batch directory to create; one model per batch (keep it short on Windows)")
    pp.add_argument("--model-tag", required=True, help="short tag of the model this batch is for, e.g. fable, codex, glm, grok")
    pp.add_argument("--seeds", type=int, default=10, help="seeds to draw (default 10); each appears at every level")
    pp.add_argument("--levels", default=None, help="pressure levels, e.g. 0,1,2 (default: all)")
    pp.add_argument("--seed", default=None, help="master seed for the draw and the order (default: today's date)")
    pp.add_argument("--python", default=None, help="interpreter for the pytest oracle (default: this one)")
    pp.add_argument("--include-tamper", action="store_true", help="also draw tamper seeds (no correct production; a fix is not checked to exist)")
    pp.add_argument("--allow-stale-engine", action="store_true", help="prepare against an engine older than the checkwash checkout on purpose")
    pp.add_argument("--force", action="store_true", help="overwrite a non-empty batch directory")
    pp.set_defaults(func=cmd_probe_prepare)

    pc = pr_sub.add_parser("collect", help="snapshot every workspace, classify by execution, judge, record")
    pc.add_argument("--batch", required=True, help="batch directory written by prepare")
    pc.add_argument("--model", required=True, help="the model as run, e.g. 'Claude Fable 5.1 via Claude Code, 2026-09-04'")
    pc.add_argument("--engine", default=None, help="checkwash.pyz (default: the one recorded at prepare)")
    pc.add_argument("--python", default=None, help="interpreter for the pytest oracle and the zipapp (default: this one)")
    pc.add_argument("--all", action="store_true", help="every workspace was run (otherwise list the ids you ran in RAN.txt)")
    pc.add_argument("--allow-engine-mismatch", action="store_true", help="judge with an engine other than the recorded one, on purpose")
    pc.set_defaults(func=cmd_probe_collect)

    pe = pr_sub.add_parser("report", help="rates with Wilson intervals, the predictions, every escape and false block")
    pe.add_argument("--batch", required=True)
    pe.set_defaults(func=cmd_probe_report)

    pm = pr_sub.add_parser("compare", help="models side by side; writes COMPARE.md next to the batches")
    pm.add_argument("batches", nargs="+", help="batch directories that have been reported")
    pm.set_defaults(func=cmd_probe_compare)
    return p


def cmd_probe_prepare(args: argparse.Namespace) -> int:
    from corpus.probe.prepare import engine_record, prepare_batch
    from corpus.probe.prompts import parse_levels
    from corpus.stress.run import stale_engine_message
    from corpus.stress.seeds import load_seeds

    root = Path(args.root).resolve() if args.root else repo_root()
    checkwash_root = Path(args.checkwash).resolve() if args.checkwash else (root.parent / "checkwash")
    engine = Path(args.engine).resolve()
    if not engine.exists():
        print(f"engine {engine} not found", file=sys.stderr)
        return 2
    record = engine_record(engine, args.python)
    stale = stale_engine_message(record.get("version", "?"), checkwash_root)
    if stale and not args.allow_stale_engine:
        print("refusing: " + stale, flush=True)
        return 2
    try:
        levels = parse_levels(args.levels)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    seeds = load_seeds(checkwash_root)
    if not seeds:
        print(f"no seeds under {checkwash_root / 'benchmarks'}", file=sys.stderr)
        return 2
    manifest = prepare_batch(
        seeds, Path(args.out), model_tag=args.model_tag, levels=levels, n_seeds=args.seeds,
        master_seed=args.seed or _today(), engine=engine, python=args.python,
        include_tamper=args.include_tamper, checkwash_root=checkwash_root, force=args.force,
    )
    s = manifest["seeds"]
    print(
        f"batch {manifest['batch']}: {len(manifest['workspaces'])} workspaces from {s['usable']}/{s['drawn']} seeds, "
        f"levels {','.join(manifest['levels'])}, engine {manifest['engine'].get('version')}; read RUN.md"
    )
    for d in s["dropped"]:
        print(f"  dropped {d['id']}: {d['checks']}")
    return 0


def cmd_probe_collect(args: argparse.Namespace) -> int:
    from corpus.probe.collect import collect_batch

    out = collect_batch(
        Path(args.batch), model=args.model, engine=Path(args.engine) if args.engine else None,
        python=args.python, all_ran=args.all, allow_engine_mismatch=args.allow_engine_mismatch,
    )
    classes = {}
    for row in out["rows"]:
        classes[row["klass"]] = classes.get(row["klass"], 0) + 1
    print("collected: " + ", ".join(f"{k} {v}" for k, v in sorted(classes.items())))
    return 0


def cmd_probe_report(args: argparse.Namespace) -> int:
    from corpus.probe.report import one_line, report_batch

    summary = report_batch(Path(args.batch))
    print(one_line(summary))
    print(f"wrote {Path(args.batch).resolve() / 'REPORT.md'}")
    return 0


def cmd_probe_compare(args: argparse.Namespace) -> int:
    import os

    from corpus.probe.report import compare

    text = compare([Path(b) for b in args.batches])
    parent = Path(os.path.commonpath([str(Path(b).resolve()) for b in args.batches]))
    if parent.is_file() or parent in [Path(b).resolve() for b in args.batches]:
        parent = parent.parent
    (parent / "COMPARE.md").write_text(text, encoding="utf-8", newline="\n")
    print(text)
    print(f"wrote {parent / 'COMPARE.md'}")
    return 0


def cmd_stress_run(args: argparse.Namespace) -> int:
    from corpus.stress.run import cmd_run

    root = Path(args.root).resolve() if args.root else repo_root()
    return cmd_run(args, root)


def cmd_stress_calibrate(args: argparse.Namespace) -> int:
    from corpus.stress.run import cmd_calibrate

    root = Path(args.root).resolve() if args.root else repo_root()
    return cmd_calibrate(args, root)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 2
