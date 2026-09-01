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
    from corpus.status import source_status, wave_status

    root, catalog = _load(args)
    waves = wave_status(root, catalog)
    for wave_id, row in waves.items():
        planned = row["catalogued"] - row["included"]
        extra = f", {planned} planned" if planned else ""
        print(
            f"{wave_id:24} {row['included']}/{row['catalogued']} catalogued{extra}; "
            f"{row['cloned']} cloned; {row['census']} census; "
            f"{row['sweeps']} sweeps; {row['prs']} harvested PRs"
        )
    if args.verbose:
        print()
        for src in catalog.sources:
            st = source_status(root, catalog, src.id)
            flag = " " if st["include"] else "*"
            print(
                f"  {flag}{st['id']:22} clone={int(st['cloned'])} "
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

    results = fetch_many(root, catalog, sources, on_progress=progress)
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
                root, catalog, src, engine=args.engine, replace=args.replace
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
    sw.add_argument("--engine", default=None, help="greenwash checkout, pyz, or executable")
    sw.add_argument("--replace", action="store_true")
    sw.set_defaults(func=cmd_sweep)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 2
