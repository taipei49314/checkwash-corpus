"""Copy hanging engine JSON/MD into the corpus ledger. Does not invent numbers."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from corpus.engine import sha256_file
from corpus.jsonio import dump, load
from corpus.paths import repo_root

FIELD_RUN_DATE = "2026-09-01"
FIELD_RUN_ID = "external-2026-09-01"
FIELD_RUN_TAG = "v0.1.49"
FIELD_RUN_ASSET = "greenwash.pyz"
EXPECTED_FIELD_RUN_SHA256 = (
    "ac6a6ea0481d49db7a35735bff0bfea2ee32957d4ebdee0aef232bb9a4a89e40"
)
WAVE0_IDS = ("attrs", "click", "flask", "httpx", "rich", "starlette")
VERDICT_FP = "false_positive"
VERDICT_SPEC = "spec_correct"
VERDICT_UNCLEAR = "unclear"

HEADING_RE = re.compile(r"^### ([A-Za-z0-9_-]+) \((\d+)\)\s*$")
SHORT_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _require_file(path: Path) -> Path:
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    return path


def _copy_text(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())


def post_field_run(*, engine_root: Path, corpus_root: Path, pyz: Path) -> Path:
    src_dir = engine_root / "benchmarks" / "external" / FIELD_RUN_DATE
    if not src_dir.is_dir():
        raise SystemExit(f"engine field-run dir missing: {src_dir}")
    digest = sha256_file(pyz)
    if digest != EXPECTED_FIELD_RUN_SHA256:
        raise SystemExit(
            f"{pyz} sha256 {digest} != v0.1.49 {FIELD_RUN_ASSET} {EXPECTED_FIELD_RUN_SHA256}"
        )
    dest_dir = corpus_root / "records" / "field-runs" / FIELD_RUN_DATE
    dest_dir.mkdir(parents=True, exist_ok=True)

    engine_record = {
        "asset": FIELD_RUN_ASSET,
        "sha256": digest,
        "tag": FIELD_RUN_TAG,
    }
    analysed = 0
    blocked = 0
    engine_errors = 0
    sweep_ids: list[str] = []

    for src in sorted(src_dir.glob("*_sweep.json")):
        payload = load(src)
        if not isinstance(payload, dict):
            raise SystemExit(f"{src.name}: not a JSON object")
        source_id = src.name[: -len("_sweep.json")]
        payload["engine"] = dict(engine_record)
        payload["field_run"] = FIELD_RUN_ID
        payload["source_id"] = source_id
        dump(dest_dir / f"{source_id}.json", payload)
        analysed += int(payload["commits_analysed"])
        blocked += int(payload["commits_blocked"])
        engine_errors += int(payload["engine_errors"])
        sweep_ids.append(source_id)

    for name in (
        "ADJUDICATION.md",
        "FINAL_REPORT.md",
        "LANDING.md",
        "OUT_OF_SAMPLE_REPORT.md",
    ):
        _copy_text(_require_file(src_dir / name), dest_dir / name)

    if analysed != 2300 or blocked != 74 or engine_errors != 0 or len(sweep_ids) != 13:
        raise SystemExit(
            f"copied totals are {len(sweep_ids)} files, {blocked}/{analysed} blocked, "
            f"engine_errors {engine_errors}; expected 13 files, 74/2300, 0 errors"
        )

    dump(
        dest_dir / "MANIFEST.json",
        {
            "id": FIELD_RUN_ID,
            "date": FIELD_RUN_DATE,
            "commits_analysed": analysed,
            "commits_blocked": blocked,
            "engine": engine_record,
            "engine_errors": engine_errors,
            "projects": len(sweep_ids),
            "source": "checkwash/benchmarks/external/2026-09-01/",
            "sources": sweep_ids,
        },
    )
    _post_field_run_adjudication(src_dir / "ADJUDICATION.md", dest_dir)
    return dest_dir


def _blocked_shas(sweep: dict) -> list[str]:
    return [str(row["commit"]) for row in sweep.get("blocked_commits") or []]


def _resolve_sha(prefix: str, blocked: list[str], source_id: str) -> str:
    matches = [sha for sha in blocked if sha.startswith(prefix)]
    if len(matches) != 1:
        raise SystemExit(f"{source_id}: {prefix!r} matched {matches} in sweep blocked set")
    return matches[0]


def _category_from_cell(cell: str) -> str:
    text = cell.strip()
    upper = text.upper()
    if upper.startswith("TP-POLICY") or text.startswith("TP-policy"):
        return VERDICT_SPEC
    if text.startswith("FP") or upper.startswith("FALSE_POSITIVE"):
        return VERDICT_FP
    if "UNCERTAIN" in upper or text.lower().startswith("unclear"):
        return VERDICT_UNCLEAR
    raise SystemExit(f"unmapped verdict cell: {cell!r}")


def _parse_table_row(line: str) -> list[str] | None:
    if not line.startswith("|"):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if not cells or set(cells[0]) <= set("-: "):
        return None
    if cells[0].lower() == "commit":
        return None
    return cells


def parse_field_run_adjudication(text: str) -> dict[str, list[dict[str, str]]]:
    """Lift per-block labels from ADJUDICATION.md. Categories mapped, reasons copied."""
    by_repo: dict[str, list[dict[str, str]]] = {}
    current: str | None = None
    default_reason = ""
    pending_reason_lines: list[str] = []
    in_table = False

    def flush_pending() -> None:
        nonlocal default_reason
        blob = " ".join(line.strip() for line in pending_reason_lines if line.strip())
        pending_reason_lines.clear()
        if blob:
            default_reason = blob

    for raw in text.splitlines():
        heading = HEADING_RE.match(raw)
        if heading:
            flush_pending()
            current = heading.group(1).lower()
            by_repo.setdefault(current, [])
            default_reason = ""
            in_table = False
            continue
        if current is None:
            continue
        if raw.startswith("|"):
            if not in_table:
                flush_pending()
            in_table = True
            cells = _parse_table_row(raw)
            if cells is None:
                continue
            prefix = cells[0].split()[0]
            if not SHORT_SHA_RE.match(prefix):
                continue
            if len(cells) == 3:
                title, verdict_cell = cells[1], cells[2]
                reason = default_reason or title
            elif len(cells) >= 4:
                title, verdict_cell, reason = cells[1], cells[2], cells[3]
                if not reason:
                    reason = default_reason or title
                elif default_reason and reason.lower() in {"fp", "tp-policy"}:
                    reason = default_reason
            else:
                raise SystemExit(f"{current}: unexpected table row {raw!r}")
            # Verdict cell may carry the reason when the table is ragged.
            if verdict_cell.startswith("FP *") or "flag" in verdict_cell.lower():
                if reason == title or not reason:
                    reason = verdict_cell
            by_repo[current].append(
                {
                    "commit_prefix": prefix,
                    "category": _category_from_cell(verdict_cell),
                    "reason": reason,
                }
            )
            continue
        if in_table and raw.strip() == "":
            in_table = False
            current = None
            continue
        if not in_table:
            pending_reason_lines.append(raw)
    flush_pending()
    return by_repo


def _post_field_run_adjudication(md_path: Path, dest_dir: Path) -> None:
    parsed = parse_field_run_adjudication(md_path.read_text(encoding="utf-8"))
    adj_dir = dest_dir / "adjudication"
    adj_dir.mkdir(parents=True, exist_ok=True)
    method = (
        "Copied from checkwash/benchmarks/external/2026-09-01/ADJUDICATION.md. "
        "Owner adopted rater-2 labels as final on 2026-09-01. "
        "TP-policy in that file is spec_correct here. Reasons are not rewritten."
    )
    for sweep_path in sweep_paths_in(dest_dir):
        sweep = load(sweep_path)
        source_id = sweep_path.stem
        blocked = _blocked_shas(sweep)
        rows = parsed.get(source_id, [])
        if not blocked and not rows:
            dump(
                adj_dir / f"{source_id}.json",
                {
                    "catalog_id": source_id,
                    "method": method + " Zero blocked commits; empty verdict set matches the sweep.",
                    "sweep_file": str(
                        sweep_path.relative_to(dest_dir.parent.parent.parent)
                    ).replace("\\", "/"),
                    "verdicts": [],
                    "wave": FIELD_RUN_ID,
                },
            )
            continue
        verdicts = []
        for row in rows:
            verdicts.append(
                {
                    "category": row["category"],
                    "commit": _resolve_sha(row["commit_prefix"], blocked, source_id),
                    "reason": row["reason"],
                }
            )
        judged = {row["commit"] for row in verdicts}
        if judged != set(blocked):
            raise SystemExit(
                f"{source_id}: adj {sorted(judged)} != blocked {sorted(set(blocked))}"
            )
        dump(
            adj_dir / f"{source_id}.json",
            {
                "catalog_id": source_id,
                "method": method,
                "sweep_file": str(
                    sweep_path.relative_to(dest_dir.parent.parent.parent)
                ).replace("\\", "/"),
                "verdicts": verdicts,
                "wave": FIELD_RUN_ID,
            },
        )


def sweep_paths_in(run_dir: Path) -> list[Path]:
    return sorted(p for p in run_dir.glob("*.json") if p.name != "MANIFEST.json")


def post_wave0_adjudication(*, engine_root: Path, corpus_root: Path) -> None:
    src = _require_file(engine_root / "benchmarks" / "adjudication-2026-08-26b.json")
    payload = load(src)
    if not isinstance(payload, dict):
        raise SystemExit(f"{src}: not a JSON object")
    method = (
        "Moved verbatim from checkwash/benchmarks/adjudication-2026-08-26b.json. "
        + str(payload.get("method") or "")
    )
    grouped: dict[str, list[dict]] = {name: [] for name in WAVE0_IDS}
    for row in payload.get("verdicts") or []:
        repo = row["repo"]
        if repo not in grouped:
            raise SystemExit(f"{src}: unexpected repo {repo!r}")
        grouped[repo].append(
            {
                "category": row["category"],
                "commit": row["commit"],
                "reason": row["reason"],
            }
        )
    for source_id, verdicts in grouped.items():
        sweep_file = f"records/sweeps/{source_id}.json"
        sweep = load(corpus_root / sweep_file)
        blocked = set(_blocked_shas(sweep))
        judged = {row["commit"] for row in verdicts}
        if judged != blocked:
            raise SystemExit(
                f"{source_id}: wave0 adj {sorted(judged)} != sweep blocked {sorted(blocked)}"
            )
        dump(
            corpus_root / "adjudication" / f"{source_id}.json",
            {
                "catalog_id": source_id,
                "method": method,
                "sweep_file": sweep_file,
                "verdicts": verdicts,
                "wave": "wave0-published-fp",
            },
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy hanging engine records into checkwash-corpus. No invented numbers."
    )
    parser.add_argument("--engine-root", required=True, type=Path)
    parser.add_argument(
        "--field-run-pyz",
        type=Path,
        required=True,
        help="v0.1.49 greenwash.pyz; sha256 is checked, not trusted from the filename",
    )
    parser.add_argument("--root", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    corpus_root = args.root.resolve() if args.root else repo_root()
    engine_root = args.engine_root.resolve()
    pyz = args.field_run_pyz.resolve()
    dest = post_field_run(engine_root=engine_root, corpus_root=corpus_root, pyz=pyz)
    post_wave0_adjudication(engine_root=engine_root, corpus_root=corpus_root)
    print(f"posted field-run into {dest.relative_to(corpus_root)}")
    print("posted wave0 adjudication for", ", ".join(WAVE0_IDS))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
