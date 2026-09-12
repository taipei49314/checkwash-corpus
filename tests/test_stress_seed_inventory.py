"""Seed inventories preserve the tree used by both materialisation and judging.

These tests use synthetic files only; they do not load or run a checkwash engine.
"""

from pathlib import Path
from types import SimpleNamespace
import stat

import pytest

from corpus.stress import inventory as I
from corpus.probe.prepare import WORKSPACE_INI, workspace_extras
from corpus.stress.common import Variant, append_extra
from corpus.stress.run import build_changes
from corpus.stress.sandbox import materialise
from corpus.stress.seeds import BASELINE_INI, PADDING_PATH, load_seeds


def write(root, files):
    for path, data in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def fixture_tree(tmp_path, kind, suite, production=None):
    case = tmp_path / "benchmarks" / kind / "cases" / "synthetic"
    prod = {"app.py": b"def answer():\r\n    return 1\r\n", "data/value.bin": b"\x00\xff\r\n"}
    prod.update(production or {})
    if kind == "refactors":
        for side in ("PROD-GOOD", "PROD-BUG"):
            write(case / side / "src", prod)
        old = case / "BEFORE"
    else:
        write(case / "src", prod)
        old = case / "before"
    write(old, {"tests/test_answer.py": b"from app import answer\r\ndef test_answer():\r\n    assert answer() == 2\r\n", **suite})
    return case, old


@pytest.mark.parametrize("kind", ["refactors", "tamper"])
def test_seed_preserves_config_helpers_and_binary_through_both_trees(tmp_path, kind):
    suite = {
        "pytest.ini": b"[pytest]\r\naddopts = --strict-markers\r\n",
        "conftest.py": b"ROOT_SETUP = 1\r\n",
        "tests/conftest.py": b"LOCAL_SETUP = 2\r\n",
        "helpers.py": b"EXPECTED = 2\r\n",
        "tests/data/answer.bin": b"\x80\x00\xff\r\n",
        "assets/answer.json": b'{"answer": 2}\r\n',
    }
    case, old = fixture_tree(tmp_path, kind, suite)
    # Metadata outside the declared roots is not part of an executable seed.
    (case / "WHY.txt").write_bytes(b"not an input")
    seed, = load_seeds(tmp_path)
    variant = append_extra(Variant.from_seed(seed), "tests/conftest.py", "NEW_SETUP = 3\n")
    changes, before, after = build_changes(seed, variant.tests, variant.extras, seed.prod_bug)
    assert [row[0] for row in changes] == ["tests/conftest.py"]
    for path, data in I.seed_tree(old).items():
        assert before[path] == data
        if path != "tests/conftest.py":
            assert after[path] == data
    assert after["tests/conftest.py"].startswith(suite["tests/conftest.py"].rstrip(b"\n"))
    assert b"NEW_SETUP = 3" in after["tests/conftest.py"]
    assert before["src/data/value.bin"] == b"\x00\xff\r\n"
    assert seed.modules == {"app"}
    assert not seed.synthetic_ini
    assert "WHY.txt" not in before
    assert PADDING_PATH in before
    materialise(tmp_path / "materialized", seed.prod_bug, variant.tests, variant.extras)
    assert I.seed_tree(tmp_path / "materialized") == after
    probe_extras = workspace_extras(seed)
    for path in ("pytest.ini", "conftest.py", "tests/conftest.py", "tests/data/answer.bin"):
        assert probe_extras[path] == seed.extras[path]


@pytest.mark.parametrize("config", ["pytest.ini", ".pytest.ini", "pytest.toml", ".pytest.toml", "pyproject.toml", "tox.ini", "setup.cfg"])
def test_existing_config_prevents_synthetic_pytest_ini_shadowing(tmp_path, config):
    contents = b"# original configuration\r\n"
    fixture_tree(tmp_path, "refactors", {config: contents})
    seed, = load_seeds(tmp_path)
    assert seed.extras[config].encode("utf-8") == contents
    assert workspace_extras(seed)[config] == seed.extras[config]
    if config != "pytest.ini":
        assert "pytest.ini" not in seed.extras


def test_seed_without_configuration_keeps_existing_fallback(tmp_path):
    fixture_tree(tmp_path, "tamper", {})
    seed, = load_seeds(tmp_path)
    assert seed.extras["pytest.ini"] == BASELINE_INI
    assert seed.synthetic_ini
    assert workspace_extras(seed)["pytest.ini"] == WORKSPACE_INI


def test_authored_baseline_spelling_is_not_replaced_by_probe_defaults(tmp_path):
    fixture_tree(tmp_path, "tamper", {"pytest.ini": BASELINE_INI.encode("utf-8"), "README.md": b"authored\n"})
    seed, = load_seeds(tmp_path)
    assert not seed.synthetic_ini
    assert workspace_extras(seed)["pytest.ini"] == BASELINE_INI
    assert workspace_extras(seed)["README.md"] == b"authored\n"


def test_production_root_config_and_assets_are_preserved(tmp_path):
    case, _ = fixture_tree(tmp_path, "refactors", {})
    config = b"[pytest]\r\naddopts = --strict-markers\r\n"
    for side in ("PROD-GOOD", "PROD-BUG"):
        write(case / side, {"pytest.ini": config, "assets/schema.bin": b"\xff\x00"})
    seed, = load_seeds(tmp_path)
    assert seed.extras["pytest.ini"].encode("utf-8") == config
    assert seed.prod_good["assets/schema.bin"] == seed.prod_bug["assets/schema.bin"] == b"\xff\x00"


def test_disagreeing_production_startup_is_rejected_unless_suite_overrides(tmp_path):
    case, old = fixture_tree(tmp_path, "refactors", {})
    write(case / "PROD-GOOD", {"pytest.ini": b"[pytest]\n"})
    with pytest.raises(I.SeedInventoryError, match="startup files disagree"):
        load_seeds(tmp_path)
    write(old, {"pytest.ini": b"[pytest]\naddopts = --strict-markers\n"})
    seed, = load_seeds(tmp_path)
    assert "--strict-markers" in seed.extras["pytest.ini"]


def test_reserved_padding_does_not_overwrite_an_authored_file(tmp_path):
    fixture_tree(tmp_path, "tamper", {PADDING_PATH: b"def test_original():\n    assert False\n"})
    with pytest.raises(I.SeedInventoryError, match="reserved padding"):
        load_seeds(tmp_path)


def test_non_utf8_editable_source_is_explicitly_rejected(tmp_path):
    fixture_tree(tmp_path, "tamper", {"conftest.py": b"# \xff\n"})
    with pytest.raises(I.SeedInventoryError, match="not UTF-8"):
        load_seeds(tmp_path)


def test_inventory_prunes_cache_and_vcs_files(tmp_path):
    write(tmp_path, {"tests/test_a.py": b"assert True\n", "__pycache__/huge.pyc": b"cache", ".git/config": b"private", "module.pyc": b"compiled"})
    assert I.seed_tree(tmp_path) == {"tests/test_a.py": b"assert True\n"}


def test_inventory_excludes_git_worktree_pointer_files(tmp_path):
    write(tmp_path, {"test_a.py": b"assert True\n", ".git": b"gitdir: /outside/repo\n"})
    assert I.seed_tree(tmp_path) == {"test_a.py": b"assert True\n"}


@pytest.mark.parametrize("limit,files", [
    ("MAX_FILE_BYTES", {"large.bin": b"12345"}),
    ("MAX_TREE_BYTES", {"a.bin": b"123", "b.bin": b"45"}),
    ("MAX_ENTRIES", {f"{i}.bin": b"" for i in range(5)}),
    ("MAX_DEPTH", {"a/b/c/d/e/file.bin": b""}),
])
def test_inventory_rejects_limits_instead_of_returning_partial_snapshot(tmp_path, monkeypatch, limit, files):
    write(tmp_path, files)
    monkeypatch.setattr(I, limit, 4)
    with pytest.raises(I.SeedInventoryError, match="limit exceeded"):
        I.seed_tree(tmp_path)


@pytest.mark.parametrize("directory", [False, True])
def test_inventory_rejects_symlinks_outside_fixture_root(tmp_path, directory):
    root = tmp_path / "fixture"
    root.mkdir()
    outside = tmp_path / "outside"
    if directory:
        outside.mkdir()
        write(outside, {"secret.bin": b"outside"})
    else:
        outside.write_bytes(b"outside")
    try:
        (root / "link").symlink_to(outside, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with pytest.raises(I.SeedInventoryError, match="link/reparse"):
        I.seed_tree(root)


def test_inventory_rejects_windows_reparse_attributes():
    info = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
    with pytest.raises(I.SeedInventoryError, match="link/reparse"):
        I._check_link(Path("fixture/junction"), info)


def test_loader_rejects_linked_case_before_reading_its_roots(tmp_path):
    cases = tmp_path / "checkout" / "benchmarks" / "tamper" / "cases"
    cases.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (cases / "linked").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with pytest.raises(I.SeedInventoryError, match="link/reparse"):
        load_seeds(tmp_path / "checkout")
