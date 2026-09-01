from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from corpus.catalog import Catalog, Source
from corpus.gitutil import GitError, clone, is_git_repo, update_existing
from corpus.paths import clone_path, clones_dir


def fetch_one(root: Path, catalog: Catalog, source: Source) -> str:
    dest = clone_path(root, source.id)
    wave = catalog.waves[source.wave]
    depth = wave.clone_depth
    pin = None
    if source.published_pin:
        pin = source.published_pin.get("newest_commit")
    clones_dir(root).mkdir(parents=True, exist_ok=True)
    if is_git_repo(dest):
        update_existing(dest, depth=depth, pin=pin)
        return f"updated {source.id}"
    if dest.exists():
        raise GitError(f"{dest} exists and is not a git clone")
    clone(source.remote, dest, depth=depth, pin=pin)
    return f"cloned {source.id}"


def fetch_many(
    root: Path,
    catalog: Catalog,
    sources: list[Source],
    *,
    on_progress: Callable[[str, str | None, str | None], None] | None = None,
) -> list[tuple[str, str | None]]:
    """Return [(id, None)] on success or [(id, error)] on failure. Fail closed
    at the caller: any error is a non-zero process."""
    results: list[tuple[str, str | None]] = []
    for source in sources:
        try:
            msg = fetch_one(root, catalog, source)
            results.append((source.id, None))
            if on_progress:
                on_progress(source.id, msg, None)
        except GitError as exc:
            results.append((source.id, str(exc)))
            if on_progress:
                on_progress(source.id, None, str(exc))
    return results
