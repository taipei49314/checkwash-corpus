"""Bounded, byte-preserving inventories of one benchmark fixture tree."""

from __future__ import annotations

import os
from pathlib import Path
import stat


MAX_ENTRIES = 4096
MAX_DEPTH = 32
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TREE_BYTES = 32 * 1024 * 1024
EXCLUDED_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".hypothesis", ".venv", "venv", "node_modules",
}


class SeedInventoryError(ValueError):
    """A fixture cannot be represented completely within the inventory contract."""


def _check_link(path: Path, info: os.stat_result) -> None:
    if stat.S_ISLNK(info.st_mode) or (
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        raise SeedInventoryError(f"seed inventory refuses link/reparse point: {path}")


def fixture_cases(checkwash_root: Path, family: str) -> list[Path]:
    """Locate direct case directories without following links in their parents."""
    current = checkwash_root
    for part in ("", "benchmarks", family, "cases"):
        if part:
            current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            return []
        _check_link(current, info)
        if not stat.S_ISDIR(info.st_mode):
            return []
    cases = []
    with os.scandir(current) as scan:
        for count, entry in enumerate(scan, start=1):
            if count > MAX_ENTRIES:
                raise SeedInventoryError(f"seed inventory entry limit exceeded: {current}")
            path = Path(entry.path)
            info = entry.stat(follow_symlinks=False)
            _check_link(path, info)
            if stat.S_ISDIR(info.st_mode):
                cases.append(path)
    return sorted(cases)


def seed_tree(root: Path) -> dict[str, bytes]:
    """Read regular files under this root; reject overflow instead of truncating.

    VCS, environment and cache directories are not fixture inputs. Links,
    junctions and special files are rejected, so the walk cannot escape the
    supplied fixture root. Limits count directory entries as well as files.
    """
    root_info = root.lstat()
    _check_link(root, root_info)
    if not stat.S_ISDIR(root_info.st_mode):
        raise SeedInventoryError(f"seed inventory root is not a directory: {root}")
    out: dict[str, bytes] = {}
    entries_seen = 0
    total_bytes = 0

    def walk(directory: Path, depth: int) -> None:
        nonlocal entries_seen, total_bytes
        if depth > MAX_DEPTH:
            raise SeedInventoryError(f"seed inventory depth limit exceeded: {directory}")
        entries = []
        with os.scandir(directory) as scan:
            for entry in scan:
                entries_seen += 1
                if entries_seen > MAX_ENTRIES:
                    raise SeedInventoryError(f"seed inventory entry limit exceeded: {root}")
                entries.append(entry)
        for entry in sorted(entries, key=lambda item: item.name):
            path = Path(entry.path)
            info = entry.stat(follow_symlinks=False)
            _check_link(path, info)
            if entry.name == ".git":
                continue
            if stat.S_ISDIR(info.st_mode):
                if entry.name not in EXCLUDED_DIRS:
                    walk(path, depth + 1)
                continue
            if not stat.S_ISREG(info.st_mode):
                raise SeedInventoryError(f"seed inventory refuses non-regular file: {path}")
            if path.suffix in {".pyc", ".pyo"}:
                continue
            budget = min(MAX_FILE_BYTES, MAX_TREE_BYTES - total_bytes)
            if info.st_size > budget:
                raise SeedInventoryError(f"seed inventory byte limit exceeded: {path}")
            with path.open("rb") as source:
                data = source.read(budget + 1)
            if len(data) > budget:
                raise SeedInventoryError(f"seed inventory byte limit exceeded: {path}")
            total_bytes += len(data)
            out[path.relative_to(root).as_posix()] = data

    walk(root, 0)
    return out
