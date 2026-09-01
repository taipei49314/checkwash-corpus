from __future__ import annotations

import subprocess
from pathlib import Path

from corpus.gitutil import clone_state, is_usable_clone
from corpus.paths import clone_dest, repo_root


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_usable_clone_is_ok(tmp_path: Path) -> None:
    repo = tmp_path / "lib"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "README").write_text("x\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init")
    assert is_usable_clone(repo, tmp_path) is True
    assert clone_state(repo, tmp_path) == "ok"


def test_half_git_is_broken(tmp_path: Path) -> None:
    leftover = tmp_path / "great_expectations"
    leftover.mkdir()
    (leftover / ".git").mkdir()
    (leftover / ".git" / "objects").mkdir()
    assert is_usable_clone(leftover, tmp_path) is False
    assert clone_state(leftover, tmp_path) == "broken"


def test_git_that_walks_up_to_corpus_is_not_a_clone(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    subprocess.run(["git", "init"], cwd=corpus, check=True, capture_output=True)
    (corpus / "README").write_text("x\n", encoding="utf-8")
    _git(corpus, "add", ".")
    _git(corpus, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init")
    nested = corpus / "clones" / "django"
    nested.mkdir(parents=True)
    assert is_usable_clone(nested, corpus) is False
    assert clone_state(nested, corpus) == "missing"


def test_bench_layout_puts_wave0_at_root() -> None:
    root = repo_root()
    assert clone_dest(root, "flask", "wave0-published-fp", "bench") == root / "flask"
    assert clone_dest(root, "django", "wave1-mock-power", "bench") == root / "clones" / "django"
    assert clone_dest(root, "flask", "wave0-published-fp", "cache") == root / "clones" / "flask"
