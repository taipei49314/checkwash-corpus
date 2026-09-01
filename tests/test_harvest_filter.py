from __future__ import annotations

from corpus.catalog import load_catalog
from corpus.harvest import _touches_tests


def test_test_paths_and_fallback() -> None:
    flask = load_catalog().source("flask")
    assert _touches_tests("tests/test_app.py", flask)
    assert _touches_tests("tests/test_app.py", flask)
    assert not _touches_tests("src/flask/app.py", flask)
    assert _touches_tests("lib/foo_test.py", flask)
    assert _touches_tests("pkg/foo.test.ts", flask)
    assert not _touches_tests("README.md", flask)


def test_sqlalchemy_test_dir() -> None:
    sa = load_catalog().source("sqlalchemy")
    assert _touches_tests("test/orm/test_query.py", sa)
    assert not _touches_tests("lib/sqlalchemy/orm.py", sa)
