from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from corpus.catalog import Catalog, Source
from corpus.gitutil import GitError, clone, clone_state, is_usable_clone, update_existing
from corpus.paths import LAYOUT_CACHE, clone_dest, clones_dir


def fetch_one(
    root: Path,
    catalog: Catalog,
    source: Source,
    *,
    layout: str = LAYOUT_CACHE,
) -> str:
    dest = clone_dest(root, source.id, source.wave, layout)
    wave = catalog.waves[source.wave]
    depth = wave.clone_depth
    pin = None
    if source.published_pin:
        pin = source.published_pin.get("newest_commit")
    clones_dir(root).mkdir(parents=True, exist_ok=True)
    if is_usable_clone(dest, root):
        update_existing(dest, depth=depth, pin=pin)
        return f"updated {source.id}"
    state = clone_state(dest, root)
    if state == "broken":
        raise GitError(
            f"{source.id}: {dest} is a broken leftover (half-written .git). "
            "Reboot and delete it, or handle.exe if Remove-Item -Force -Recurse fails"
        )
    if dest.exists() and any(dest.iterdir()):
        raise GitError(f"{dest} exists and is not a usable git clone")
    clone(source.remote, dest, depth=depth, pin=pin)
    return f"cloned {source.id}"


def fetch_many(
    root: Path,
    catalog: Catalog,
    sources: list[Source],
    *,
    layout: str = LAYOUT_CACHE,
    on_progress: Callable[[str, str | None, str | None], None] | None = None,
) -> list[tuple[str, str | None]]:
    results: list[tuple[str, str | None]] = []
    for source in sources:
        try:
            msg = fetch_one(root, catalog, source, layout=layout)
            results.append((source.id, None))
            if on_progress:
                on_progress(source.id, msg, None)
        except (GitError, OSError, ValueError) as exc:
            results.append((source.id, str(exc)))
            if on_progress:
                on_progress(source.id, None, str(exc))
    return results
