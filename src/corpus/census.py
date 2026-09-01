from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from corpus.catalog import Catalog, Source
from corpus.gitutil import GitError, git, has_commit, head_sha
from corpus.jsonio import dump
from corpus.paths import census_path, inspect_clone, resolve_clone

# Binary / generated paths we do not open. Segment-anchored, like greenwash.
_SKIP_PARTS = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
    }
)
_SKIP_SUFFIXES = frozenset(
    {".pyc", ".so", ".dll", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".whl"}
)


def _walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(root).parts)
        if rel_parts & _SKIP_PARTS:
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
        except OSError:
            continue
        out.append(path)
    return out


def _count_regex(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text))


def _is_js_test(rel: str, globs_as_suffixes: tuple[str, ...]) -> bool:
    lower = rel.replace("\\", "/").lower()
    return any(lower.endswith(suf) for suf in globs_as_suffixes)


def _js_suffixes(globs: list[str]) -> tuple[str, ...]:
    # Catalog stores gitignore-style globs; census matches on suffix.
    out: list[str] = []
    for g in globs:
        if g.startswith("**/"):
            out.append(g[3:].lower())
        else:
            out.append(g.lower())
    return tuple(out)


def _dir_bytes(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.stat().st_size
        except OSError:
            continue
    return total


def census_clone(repo: Path, source: Source, catalog: Catalog, revision: str) -> dict[str, Any]:
    probes = catalog.power_probes
    patch_re = probes["patch"]
    unittest_re = probes["unittest_assert"]
    approx_re = probes["approx"]
    skip_re = probes["skip"]
    js_suf = _js_suffixes(list(probes["js_test_globs"]))
    runner_names = set(probes.get("runner_names") or [])

    patch_sites = 0
    unittest_asserts = 0
    approx_sites = 0
    skip_sites = 0
    js_test_files = 0
    py_files = 0
    runner_files = 0
    files_scanned = 0

    for path in _walk_files(repo):
        rel = path.relative_to(repo).as_posix()
        name = path.name
        if name in runner_names or name.endswith(".mk") or name.endswith(".mak"):
            runner_files += 1
        if _is_js_test(rel, js_suf):
            js_test_files += 1
        if path.suffix not in {".py", ".pyi", ".js", ".jsx", ".ts", ".tsx"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files_scanned += 1
        if path.suffix == ".py":
            py_files += 1
            patch_sites += _count_regex(text, patch_re)
            unittest_asserts += _count_regex(text, unittest_re)
            approx_sites += _count_regex(text, approx_re)
            skip_sites += _count_regex(text, skip_re)

    wave = catalog.waves[source.wave]
    return {
        "catalog_id": source.id,
        "wave": source.wave,
        "owner_repo": source.owner_repo,
        "revision": revision,
        "clone_depth": wave.clone_depth,
        "bytes_on_disk": _dir_bytes(repo),
        "probes": {
            "patch": patch_re,
            "unittest_assert": unittest_re,
            "approx": approx_re,
            "skip": skip_re,
            "js_test_globs": list(probes["js_test_globs"]),
        },
        "counts": {
            "files_scanned": files_scanned,
            "py_files": py_files,
            "patch_sites": patch_sites,
            "unittest_asserts": unittest_asserts,
            "approx_sites": approx_sites,
            "skip_sites": skip_sites,
            "js_test_files": js_test_files,
            "runner_files": runner_files,
        },
        "prior_power": source.prior_power,
    }


def run_census(root: Path, catalog: Catalog, source: Source) -> Path:
    repo = resolve_clone(root, source.id)
    if repo is None:
        state, path = inspect_clone(root, source.id)
        if state == "broken":
            raise GitError(
                f"{source.id}: {path} is a broken leftover, not a clone"
            )
        raise GitError(f"{source.id}: clone missing at {path}")
    revision = head_sha(repo)
    if source.published_pin:
        pin = source.published_pin["newest_commit"]
        if not has_commit(repo, pin):
            raise GitError(f"{source.id}: clone does not contain published pin {pin}")
        # Wave 0 census is of the published window's newest commit, not whatever HEAD drifted to.
        git(repo, "checkout", "--detach", pin)
        revision = pin
    record = census_clone(repo, source, catalog, revision)
    dest = census_path(root, source.id)
    dump(dest, record)
    return dest
