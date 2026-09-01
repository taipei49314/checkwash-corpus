from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from corpus.engine import EngineError, resolve_engine, sha256_file


def test_pyz_is_accepted(tmp_path: Path) -> None:
    pyz = tmp_path / "checkwash.pyz"
    with zipfile.ZipFile(pyz, "w") as zf:
        zf.writestr("__main__.py", "print('ok')\n")
    argv, record = resolve_engine(str(pyz), allow_dirty=False)
    assert argv[-1] == str(pyz.resolve())
    assert record["asset"] == "checkwash.pyz"
    assert record["sha256"] == sha256_file(pyz)
    assert len(record["sha256"]) == 64


def test_old_greenwash_pyz_is_accepted(tmp_path: Path) -> None:
    pyz = tmp_path / "greenwash.pyz"
    with zipfile.ZipFile(pyz, "w") as zf:
        zf.writestr("__main__.py", "print('ok')\n")
    _, record = resolve_engine(str(pyz), allow_dirty=False)
    assert record["asset"] == "greenwash.pyz"


def test_unknown_pyz_name_is_rejected(tmp_path: Path) -> None:
    pyz = tmp_path / "other.pyz"
    with zipfile.ZipFile(pyz, "w") as zf:
        zf.writestr("__main__.py", "print('ok')\n")
    with pytest.raises(EngineError, match="known release asset"):
        resolve_engine(str(pyz), allow_dirty=False)


def test_checkout_refused_without_dirty_flag(tmp_path: Path) -> None:
    checkout = tmp_path / "src-tree"
    (checkout / "src" / "checkwash").mkdir(parents=True)
    (checkout / "src" / "checkwash" / "__init__.py").write_text("", encoding="utf-8")
    with pytest.raises(EngineError, match="dirty engine"):
        resolve_engine(str(checkout), allow_dirty=False)
    argv, record = resolve_engine(str(checkout), allow_dirty=True)
    assert record["asset"] == "editable"
    assert record["sha256"] is None
    assert argv[-1] == "checkwash"
