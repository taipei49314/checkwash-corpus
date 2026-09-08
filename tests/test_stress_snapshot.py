"""The stress adapter must judge the same complete tree as the released CLI.

Engine integration runs are opt-in with CORPUS_TEST_ENGINE_PYZ on the pool;
no engine is downloaded or repinned by these tests.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from corpus.stress.engine import Engine, TODAY, blackbox_check
from corpus.stress.run import _corpus_changes, _tree, build_changes
from corpus.stress.seeds import Seed


def test_complete_tree_keeps_unchanged_tests_config_and_deletions():
    seed = Seed('synthetic', 'refactors', {'src/app.py': b'x = 1'}, None,
                {'tests/test_a.py': 'assert True', 'tests/test_b.py': 'assert True'},
                'tests/test_a.py', {'app'}, {'pytest.ini': '[pytest]\naddopts = --strict-markers'})
    changes, before, after = build_changes(seed, {'tests/test_a.py': None}, {}, seed.prod_bug)
    assert after['tests/test_b.py'] == before['tests/test_b.py']
    assert after['pytest.ini'] == before['pytest.ini']
    assert after['tests/test_a.py'] is None
    assert changes == [('tests/test_a.py', b'assert True', None)]


def test_calibration_inventory_includes_non_python_config(tmp_path):
    before, after = tmp_path / 'before', tmp_path / 'after'
    before.mkdir(); after.mkdir()
    (before / 'pytest.ini').write_bytes(b'[pytest]\n')
    (after / 'pytest.ini').write_bytes(b'[pytest]\npython_functions = never_*\n')
    (before / 'conftest.py').write_bytes(b'import pytest\n')
    assert _tree(after) == {'pytest.ini': b'[pytest]\npython_functions = never_*\n'}
    assert _corpus_changes(before, after) == [
        ('conftest.py', b'import pytest\n', None),
        ('pytest.ini', b'[pytest]\n', b'[pytest]\npython_functions = never_*\n'),
    ]


@pytest.fixture(scope='module')
def engine():
    path = os.environ.get('CORPUS_TEST_ENGINE_PYZ')
    if not path:
        pytest.skip('pool integration requires CORPUS_TEST_ENGINE_PYZ')
    return Engine(Path(path))


def parity(engine, tmp_path, before, after, expected):
    changes = [(p, before.get(p), after.get(p)) for p in sorted(before.keys() | after.keys())
               if before.get(p) != after.get(p)]
    judged, stable = engine.judge_twice(changes, after, {'app'})
    assert stable and judged.verdict == expected, (judged.verdict, judged.rules, judged.error)
    cli, note = blackbox_check(engine.pyz, tmp_path, before, after)
    assert cli == judged.verdict, (cli, note, judged.verdict, judged.rules)
    proc = subprocess.run([sys.executable, str(engine.pyz), 'check', 'HEAD~1..HEAD', '--format', 'json'],
                          cwd=tmp_path, capture_output=True, timeout=120,
                          env=dict(os.environ, CHECKWASH_TODAY=TODAY.isoformat()))
    payload = json.loads(proc.stdout)
    rules = sorted({f"{f['rule']}/{f['severity']}" for f in payload['findings'] if not f.get('allowlisted')})
    assert rules == judged.rules


def test_first_party_patch_is_not_a_declared_third_party(engine, tmp_path):
    tests = b'''from unittest.mock import patch
from app.prod import safe_divide
def test_divide():
    assert safe_divide(6, 2) == 3
'''
    before = {'src/app/__init__.py': b'', 'src/app/prod.py': b'def safe_divide(a, b):\n    return a / b\n',
              'tests/test_prod.py': tests}
    after = {**before, 'tests/test_prod.py': tests.replace(b'    assert',
             b"    with patch('app.prod.safe_divide', return_value=3):\n        assert")}
    parity(engine, tmp_path, before, after, 'block')


@pytest.mark.parametrize('config,expected', [(b'[pytest]\n', 'pass'),
                                           (b'[pytest]\npython_functions = never_*\n', 'block')])
def test_unchanged_config_is_present_in_strict_snapshot(engine, tmp_path, config, expected):
    before = {'src/app/__init__.py': b'', 'src/app/prod.py': b'def double(x):\n    return x * 2\n',
              'pytest.ini': config,
              'tests/test_prod.py': b'''from app.prod import double
def test_one():
    assert double(1) == 2
def test_two():
    assert double(2) == 4
'''}
    after = {**before, 'tests/test_prod.py': b'''from app.prod import double
import pytest
@pytest.mark.parametrize("x,expected", [(1, 2), (2, 4)])
def test_double(x, expected):
    assert double(x) == expected
'''}
    parity(engine, tmp_path, before, after, expected)


@pytest.mark.parametrize('kind,name,expected', [
    ('refactors', 'CASE_026_leap', 'pass'),
    ('refactors', 'CASE_029_flatten', 'pass'),
    ('tamper', '026-normalize', 'block'),
])
def test_reported_calibration_divergences(engine, tmp_path, kind, name, expected):
    root = os.environ.get('CORPUS_TEST_CHECKWASH_ROOT')
    if not root:
        pytest.skip('pool integration requires CORPUS_TEST_CHECKWASH_ROOT')
    case = Path(root) / 'benchmarks' / kind / 'cases' / name
    if kind == 'refactors':
        prod, old, new = _tree(case / 'PROD-GOOD'), _tree(case / 'BEFORE'), _tree(case / 'AFTER')
    else:
        prod = {f'src/{p}': b for p, b in _tree(case / 'src').items()}
        old, new = _tree(case / 'before'), _tree(case / 'after')
    assert old and new and prod
    parity(engine, tmp_path, {**prod, **old}, {**prod, **new}, expected)
