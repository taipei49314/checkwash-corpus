"""Replica silent-suite gate. Exit 0 is not enough if nothing ran."""
from __future__ import annotations

import re
import subprocess
import sys

_PASSED_RE = re.compile(r"(\d+)\s+passed")


def _run_suite(suite: str) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", suite, "-q", "--tb=line"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
    low = out.lower()
    if "no tests ran" in low or re.search(r"collected 0 items", low):
        return 1, "FAIL collected 0 items (silent suite)"
    m = _PASSED_RE.search(out)
    n_pass = int(m.group(1)) if m else None
    if r.returncode == 0 and n_pass == 0:
        return 1, "FAIL 0 passed (silent suite)"
    if r.returncode == 0 and n_pass is None and "passed" not in low:
        return 1, "FAIL no pytest summary (silent suite)"
    tail = out.splitlines()[-1] if out.splitlines() else "(no output)"
    if r.returncode != 0:
        return r.returncode, tail
    return 0, tail if n_pass is None else f"{n_pass} passed"


def main() -> int:
    code, tail = _run_suite("tests")
    mark = "ok " if code == 0 else "FAIL"
    print(f"  {mark} tests  {tail}")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
