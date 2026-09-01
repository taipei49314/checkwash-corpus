"""Harvest merged GitHub PRs that touch test files.

Uses `gh`. A missing `gh` is a tool error (exit 2), not a silent empty harvest.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from corpus.catalog import Catalog, Source
from corpus.jsonio import dump, load
from corpus.paths import prs_dir

MAX_PATCH_CHARS = 50_000
MAX_PR_CHARS = 200_000

_TEST_FILE_RE = re.compile(
    r"(^|/)("
    r"test_[^/]+\.py"
    r"|[^/]+_test\.py"
    r"|conftest\.py"
    r"|[^/]+\.test\.[jt]sx?"
    r"|[^/]+\.spec\.[jt]sx?"
    r")$",
    re.I,
)


class HarvestError(RuntimeError):
    pass


def _gh(*args: str) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip() or proc.stdout.decode("utf-8", "replace").strip()
        raise HarvestError(f"gh {' '.join(args)} failed: {err}")
    return proc.stdout.decode("utf-8", "replace")


def _gh_json(*args: str) -> Any:
    return json.loads(_gh(*args) or "null")


def _touches_tests(filename: str, source: Source) -> bool:
    path = filename.replace("\\", "/")
    for prefix in source.test_paths:
        p = prefix.replace("\\", "/").rstrip("/") + "/"
        if path.startswith(p) or path == prefix.rstrip("/"):
            return True
    return bool(_TEST_FILE_RE.search(path))


def _identity_path(dest: Path, number: int, sha: str) -> Path:
    short = sha[:12] if sha else "unknown"
    return dest / f"{number}-{short}.json"


def _already_have(dest: Path, number: int, sha: str) -> bool:
    path = _identity_path(dest, number, sha)
    if not path.is_file():
        return False
    try:
        data = load(path)
    except (OSError, json.JSONDecodeError):
        return False
    return data.get("head_sha") == sha and data.get("pr_number") == number


def harvest_source(
    root: Path,
    source: Source,
    *,
    per_repo: int,
    harvested_on: str,
) -> dict[str, int]:
    dest = prs_dir(root, source.id)
    dest.mkdir(parents=True, exist_ok=True)
    listed = _gh_json(
        "pr",
        "list",
        "--repo",
        source.owner_repo,
        "--state",
        "merged",
        "--limit",
        str(per_repo),
        "--json",
        "number,title,url,mergedAt,headRefOid",
    )
    if not isinstance(listed, list):
        raise HarvestError(f"{source.id}: unexpected gh pr list payload")
    kept = 0
    skipped_identity = 0
    scanned = 0
    for pr in listed:
        scanned += 1
        number = int(pr["number"])
        sha = str(pr.get("headRefOid") or "")
        if _already_have(dest, number, sha):
            skipped_identity += 1
            continue
        files = _gh_json("api", f"repos/{source.owner_repo}/pulls/{number}/files", "--paginate")
        if not isinstance(files, list):
            files = []
        test_files = [f for f in files if _touches_tests(str(f.get("filename") or ""), source)]
        if not test_files:
            continue
        patches: list[dict[str, Any]] = []
        total = 0
        for fobj in test_files:
            patch = str(fobj.get("patch") or "")
            if len(patch) > MAX_PATCH_CHARS:
                patch = patch[:MAX_PATCH_CHARS] + "\n… [truncated]\n"
            total += len(patch)
            if total > MAX_PR_CHARS:
                break
            patches.append(
                {
                    "filename": fobj.get("filename"),
                    "status": fobj.get("status"),
                    "additions": fobj.get("additions"),
                    "deletions": fobj.get("deletions"),
                    "patch": patch,
                }
            )
        record = {
            "catalog_id": source.id,
            "wave": source.wave,
            "owner_repo": source.owner_repo,
            "pr_number": number,
            "head_sha": sha,
            "title": pr.get("title"),
            "url": pr.get("url"),
            "merged_at": pr.get("mergedAt"),
            "harvested_on": harvested_on,
            "test_files": patches,
            "test_file_count": len(test_files),
            "changed_file_count": len(files),
            "note": "test-file excerpts only; not a checkwash verdict",
        }
        dump(_identity_path(dest, number, sha), record)
        kept += 1
    return {
        "scanned": scanned,
        "kept": kept,
        "skipped_identity": skipped_identity,
    }
