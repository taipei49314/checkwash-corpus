"""`stress run` and `stress calibrate` refuse an engine older than the checkout.

The 2026-09-03 LLM-arm run spent five hours judging with the v0.2.8 zipapp that
sat at the repository root while ../checkwash was at v0.2.12. Nothing in the
harness noticed. The guard is a pure function over two version strings and a
pyproject; the CLI flag `--allow-stale-engine` is the deliberate override.
"""

from pathlib import Path

from corpus.stress.run import checkout_version, stale_engine_message


def _checkout(tmp_path: Path, version: str) -> Path:
    root = tmp_path / "checkwash"
    root.mkdir()
    (root / "pyproject.toml").write_text(f'[project]\nname = "checkwash"\nversion = "{version}"\n', encoding="utf-8")
    return root


def test_reads_the_checkout_version(tmp_path):
    assert checkout_version(_checkout(tmp_path, "0.2.12")) == "0.2.12"
    assert checkout_version(tmp_path / "missing") is None


def test_older_engine_is_refused_with_the_fix_in_the_message(tmp_path):
    root = _checkout(tmp_path, "0.2.12")
    msg = stale_engine_message("0.2.8", root)
    assert msg and "0.2.8" in msg and "0.2.12" in msg and "--allow-stale-engine" in msg


def test_equal_or_newer_engine_passes(tmp_path):
    root = _checkout(tmp_path, "0.2.12")
    assert stale_engine_message("0.2.12", root) is None
    assert stale_engine_message("0.2.13", root) is None
    assert stale_engine_message("0.10.0", root) is None  # numeric, not lexical


def test_no_checkout_means_no_opinion(tmp_path):
    assert stale_engine_message("0.2.8", tmp_path / "nowhere") is None
    assert stale_engine_message("?", _checkout(tmp_path, "0.2.12")) is None
