"""Poll taipei49314/checkwash. Print one DONE line only when HEAD or the
latest Release zipapp actually changes. No progress output.

Triggers:
  DONE release <tag> <pyz-sha256>
  DONE commit <sha> <subject>
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = "taipei49314/checkwash"
INTERVAL_SEC = 120
STATE_PATH = Path(__file__).resolve().parent / ".watch-state.json"


def _gh_json(*args: str):
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gh failed")
    return json.loads(proc.stdout)


def snapshot() -> dict:
    commit = _gh_json(
        "api",
        f"repos/{REPO}/commits/main",
        "--jq",
        "{sha:.sha, msg:.commit.message}",
    )
    subject = str(commit.get("msg") or "").splitlines()[0][:80]
    try:
        release = _gh_json(
            "release",
            "view",
            "--repo",
            REPO,
            "--json",
            "tagName,assets",
        )
    except RuntimeError:
        release = {"tagName": "", "assets": []}
    pyz = ""
    for asset in release.get("assets") or []:
        if asset.get("name") == "checkwash.pyz":
            digest = str(asset.get("digest") or "")
            pyz = digest.removeprefix("sha256:")
            break
    return {
        "sha": commit.get("sha") or "",
        "subject": subject,
        "tag": release.get("tagName") or "",
        "pyz": pyz,
    }


def load_state() -> dict:
    if STATE_PATH.is_file():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(data: dict) -> None:
    STATE_PATH.write_text(json.dumps(data, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    failures = 0
    while True:
        try:
            now = snapshot()
            failures = 0
        except Exception as exc:
            failures += 1
            if failures >= 5:
                print(f"FAILED {exc}", flush=True)
                return 1
            time.sleep(INTERVAL_SEC)
            continue
        prev = load_state()
        if not prev:
            save_state(now)
            time.sleep(INTERVAL_SEC)
            continue
        if now["tag"] and now["tag"] != prev.get("tag"):
            print(f"DONE release {now['tag']} {now['pyz']}", flush=True)
        elif now["pyz"] and now["pyz"] != prev.get("pyz"):
            print(f"DONE release {now['tag']} {now['pyz']}", flush=True)
        elif now["sha"] and now["sha"] != prev.get("sha"):
            print(f"DONE commit {now['sha']} {now['subject']}", flush=True)
        save_state(now)
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    raise SystemExit(main())
