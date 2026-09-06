"""CLI vs in-process checkwash on the chassis replica.

Same discipline as `corpus.stress.engine`: in-process `analyze()` from the
pinned zipapp, then `blackbox_check` on a two-commit git repo. Divergence
is a finding, not a silent pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from corpus.stress.engine import Engine, blackbox_check


@dataclass(frozen=True)
class ParityResult:
    embedded: str | None
    cli: str | None
    note: str
    divergence: bool


def replica_changes(before: dict[str, bytes], after: dict[str, bytes | None]) -> tuple[
    list[tuple[str, bytes | None, bytes | None]],
    dict[str, bytes],
    set[str],
]:
    """`head` is the after tree (existing files). `changes` is the diff."""
    after_full: dict[str, bytes | None] = dict(before)
    after_full.update(after)
    changes: list[tuple[str, bytes | None, bytes | None]] = []
    head: dict[str, bytes] = {}
    for path in sorted(set(before) | set(after_full)):
        b = before.get(path)
        a = after_full.get(path)
        if a is None:
            if b is not None:
                changes.append((path, b, None))
            continue
        head[path] = a
        if b != a:
            changes.append((path, b, a))
    return changes, head, {"app"}


def check_parity(
    pyz: Path,
    before: dict[str, bytes],
    after: dict[str, bytes | None],
    work: Path,
    python: str | None = None,
) -> ParityResult:
    engine = Engine(pyz)
    changes, head, modules = replica_changes(before, after)
    embedded = engine.judge(changes, head, modules)
    cli, note = blackbox_check(pyz, work, before, after, python=python)
    divergence = cli is not None and embedded.verdict != cli
    return ParityResult(
        embedded=embedded.verdict,
        cli=cli,
        note=note,
        divergence=divergence,
    )
