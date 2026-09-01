from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path


class GitError(RuntimeError):
    pass


def git(repo: Path | str, *args: str, check: bool = True) -> str:
    cmd = ["git", "-C", str(repo), *args]
    proc = subprocess.run(cmd, capture_output=True)
    if check and proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip() or proc.stdout.decode("utf-8", "replace").strip()
        raise GitError(f"git {' '.join(args)} failed in {repo}: {err}")
    return proc.stdout.decode("utf-8", "replace")


def git_bytes(repo: Path | str, *args: str, check: bool = True) -> bytes:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if check and proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"git {' '.join(args)} failed in {repo}: {err}")
    return proc.stdout


def is_git_repo(path: Path) -> bool:
    return path.is_dir() and ((path / ".git").exists() or (path / ".git").is_file())


def has_commit(repo: Path, sha: str) -> bool:
    if not sha:
        return False
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
        capture_output=True,
    )
    return proc.returncode == 0


def head_sha(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").strip()


def _rmtree(path: Path) -> None:
    if not path.exists():
        return
    shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        time.sleep(1)
        shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        raise GitError(f"could not remove {path} (Windows file lock)")


def clone(
    remote: str,
    dest: Path,
    *,
    depth: int = 0,
    pin: str | None = None,
    attempts: int = 3,
) -> None:
    """Clone into dest. depth 0 means a full clone (wave 0 pins may be old).

    Clones directly into dest (no tmp rename) so Windows cannot fail the
    last step after a successful fetch. Network errors retry with backoff.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    leftover = dest.parent / f".tmp-{dest.name}"
    _rmtree(leftover)
    args = ["git", "clone"]
    if depth > 0:
        args += ["--depth", str(depth), "--single-branch"]
    last_err = ""
    for attempt in range(1, attempts + 1):
        _rmtree(dest)
        proc = subprocess.run([*args, remote, str(dest)], capture_output=True)
        if proc.returncode == 0:
            if pin:
                _ensure_pin(dest, pin, depth=depth)
                git(dest, "checkout", "--detach", pin)
            return
        last_err = proc.stderr.decode("utf-8", "replace").strip()
        _rmtree(dest)
        if attempt < attempts:
            time.sleep(5 * attempt)
    raise GitError(f"git clone {remote} failed after {attempts} attempts: {last_err}")


def _ensure_pin(repo: Path, pin: str, *, depth: int) -> None:
    if has_commit(repo, pin):
        return
    # GitHub allows fetching a SHA. Depth 0: unbounded. Else deepen.
    fetch_args = ["fetch", "origin", pin]
    if depth > 0:
        fetch_args = ["fetch", "--depth", str(max(depth, 400)), "origin", pin]
    try:
        git(repo, *fetch_args)
    except GitError:
        git(repo, "fetch", "--unshallow")
        git(repo, "fetch", "origin", pin)
    if not has_commit(repo, pin):
        raise GitError(f"{repo} still missing pin {pin} after fetch")


def update_existing(repo: Path, *, depth: int, pin: str | None) -> None:
    if pin:
        _ensure_pin(repo, pin, depth=depth)
        git(repo, "checkout", "--detach", pin)
        return
    git(repo, "fetch", "--update-head-ok", "origin")
    # Stay on whatever the clone already had if we cannot name a default branch.
    proc = subprocess.run(
        ["git", "-C", str(repo), "symbolic-ref", "refs/remotes/origin/HEAD"],
        capture_output=True,
    )
    if proc.returncode == 0:
        ref = proc.stdout.decode("utf-8", "replace").strip()
        branch = ref.rsplit("/", 1)[-1]
        git(repo, "checkout", branch, check=False)
        git(repo, "merge", "--ff-only", f"origin/{branch}", check=False)
