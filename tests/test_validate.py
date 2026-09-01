from __future__ import annotations

from corpus.cli import main
from corpus.validate import validate


def test_validate_clean_checkout() -> None:
    errors = validate()
    assert errors == [], errors


def test_cli_validate_exits_zero() -> None:
    assert main(["validate"]) == 0


def test_cli_status_exits_zero() -> None:
    assert main(["status"]) == 0
