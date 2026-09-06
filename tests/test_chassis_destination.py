"""Replica writes require an unused destination and preserve rejected inputs."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from corpus.chassis.replica import KINDS, replica_tree, write_replica
from corpus.cli import main


def snapshot(root: Path) -> dict[str, bytes | None]:
    return {p.relative_to(root).as_posix(): p.read_bytes() if p.is_file() else None
            for p in root.rglob("*")}


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("existing", [False, True])
def test_new_or_empty_destination_has_exact_replica_bytes(tmp_path: Path, kind: str, existing: bool):
    dest = tmp_path / "replica"
    if existing:
        dest.mkdir()
    assert write_replica(dest, kind) == dest
    files = {p.relative_to(dest).as_posix(): p.read_bytes() for p in dest.rglob("*") if p.is_file()}
    assert files == replica_tree(kind)


@pytest.mark.parametrize("content", ["sentinel", "hidden", "empty-child", "existing-replica"])
def test_nonempty_destination_is_rejected_without_changes(tmp_path: Path, content: str):
    dest = tmp_path / "replica"
    dest.mkdir()
    if content == "existing-replica":
        write_replica(dest, "collect_zero")
    elif content == "empty-child":
        (dest / "empty").mkdir()
    else:
        (dest / (".keep" if content == "hidden" else "pytest.ini")).write_bytes(b"user-owned bytes\r\n")
    before = snapshot(dest)

    with pytest.raises(ValueError, match="destination"):
        write_replica(dest, "passing")

    assert snapshot(dest) == before


def test_file_destination_is_rejected_without_changes(tmp_path: Path):
    dest = tmp_path / "file"
    dest.write_bytes(b"existing file\x00")
    with pytest.raises(ValueError, match="destination"):
        write_replica(dest, "passing")
    assert dest.read_bytes() == b"existing file\x00"


@pytest.mark.parametrize("dangling", [False, True])
def test_destination_symlink_is_rejected_without_writing_target(tmp_path: Path, dangling: bool):
    target = tmp_path / "target"
    if not dangling:
        target.mkdir()
    dest = tmp_path / "link"
    try:
        dest.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink unavailable: {exc}")
    with pytest.raises(ValueError, match="destination"):
        write_replica(dest, "passing")
    assert dest.is_symlink()
    assert target.exists() is not dangling
    if not dangling:
        assert snapshot(target) == {}


def test_destination_reparse_attribute_is_rejected(tmp_path: Path, monkeypatch):
    dest = tmp_path / "reparse"
    dest.mkdir()
    original = Path.lstat

    def fake_lstat(path, *args, **kwargs):
        if path == dest:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(ValueError, match="destination"):
        write_replica(dest, "passing")
    assert snapshot(dest) == {}


def test_invalid_kind_does_not_create_destination(tmp_path: Path):
    dest = tmp_path / "new"
    with pytest.raises(ValueError, match="unknown replica kind"):
        write_replica(dest, "unknown")
    assert not dest.exists()


def test_cli_rejects_nonempty_destination_with_input_error(tmp_path: Path, capsys):
    dest = tmp_path / "replica"
    dest.mkdir()
    (dest / "keep").write_bytes(b"keep")
    assert main(["chassis", "materialise", str(dest), "--kind", "passing"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "destination" in captured.err and str(dest) in captured.err
    assert snapshot(dest) == {"keep": b"keep"}


def test_cli_reports_io_failure_without_success(tmp_path: Path, monkeypatch, capsys):
    from corpus.chassis import replica

    def unavailable(*args):
        raise OSError("filesystem unavailable")

    monkeypatch.setattr(replica, "materialise", unavailable)
    assert main(["chassis", "materialise", str(tmp_path / "new"), "--kind", "passing"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "filesystem unavailable" in captured.err
