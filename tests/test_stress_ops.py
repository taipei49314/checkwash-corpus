"""The operator libraries must produce parseable, surgical edits — or decline.

No checkwash checkout, no pytest subprocess, no engine: a synthetic seed and
every (operator, spelling) pair. What is pinned: an operator either returns
None (not applicable) or a variant whose main test file still parses and
whose diff against the seed is local — a whole-file rewrite would make the
harness's own reformatting indistinguishable from the engine's verdict.
"""

from __future__ import annotations

import ast
import difflib
import random

import pytest

from corpus.stress import honest_ops, random_ops, tamper_ops
from corpus.stress.common import add_ini_option
from corpus.stress.edits import add_first_param
from corpus.stress.run import apply_chain
from corpus.stress.seeds import BASELINE_INI, PADDING, PADDING_PATH, Seed

MAIN = "tests/test_clamp.py"
SOURCE = '''from app.clamp import clamp, label


def test_clamp_inside():
    value = 5
    assert clamp(value, 0, 10) == 5


def test_clamp_above():
    assert clamp(15, 0, 10) == 10
    assert clamp(15.5, 0, 10) == 10.0


def test_label():
    assert label('x') == 'X'
'''


def _seed() -> Seed:
    prod = {
        "src/app/__init__.py": b"",
        "src/app/clamp.py": b"def clamp(x, lo, hi):\n    return max(lo, min(x, hi))\n\n\ndef label(s):\n    return s.upper()\n",
    }
    return Seed(
        id="synthetic/clamp", origin="refactors", prod_bug=prod, prod_good=prod,
        tests={MAIN: SOURCE, PADDING_PATH: PADDING}, main_test=MAIN, modules={"app"},
        extras={"pytest.ini": BASELINE_INI},
    )


def _pairs(registry):
    return [(name, sp) for name, (_fam, spellings, _fn) in sorted(registry.items()) for sp in spellings]


ALL = [("tamper", p) for p in _pairs(tamper_ops.OPS)] + [("honest", p) for p in _pairs(honest_ops.OPS)] + [("open", p) for p in _pairs(random_ops.OPS)]


@pytest.mark.parametrize("kind,pair", ALL, ids=lambda v: v if isinstance(v, str) else f"{v[0]}.{v[1]}")
def test_operator_is_parseable_and_surgical(kind, pair):
    registry = {"tamper": tamper_ops.OPS, "honest": honest_ops.OPS, "open": random_ops.OPS}[kind]
    seed = _seed()
    applied = 0
    for trial in range(10):
        variant = apply_chain(seed, registry, [pair], "unit", trial)
        if variant is None:
            continue
        applied += 1
        src = variant.tests[MAIN]
        ast.parse(src)  # every emitted file must be Python
        for path, text in variant.extras.items():
            assert text.strip(), path
        if src != SOURCE:
            diff = [line for line in difflib.unified_diff(SOURCE.splitlines(), src.splitlines(), lineterm="", n=0) if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
            # local: a single operator touches a handful of lines, not the file
            assert len(diff) <= 30, (pair, diff)
    # every operator applies to *something* on this seed except the shape-gated ones
    shape_gated = {("tamper", ("neutralize_context", "assertraises_self")), ("tamper", ("neutralize_context", "assertraisesregex_self"))}
    if (kind, pair) not in shape_gated:
        assert applied > 0, f"{kind} {pair} never applied to the synthetic seed"


def test_add_ini_option_appends_addopts():
    ini = add_ini_option(BASELINE_INI, "addopts", "--collect-only")
    assert "addopts = --collect-only" in ini
    ini = add_ini_option(ini, "addopts", '-k "not x"')
    assert 'addopts = --collect-only -k "not x"' in ini
    assert ini.count("[pytest]") == 1
    assert "testpaths = tests" in ini


def test_add_first_param_shapes():
    assert add_first_param("def test_x():", "_u") == "def test_x(_u):"
    assert add_first_param("def test_x(a, b):", "_u") == "def test_x(_u, a, b):"
    assert add_first_param("    def test_x(self):", "_u") == "    def test_x(self, _u):"
    assert add_first_param("    def test_x(self, a):", "_u") == "    def test_x(self, _u, a):"


def test_chain_is_deterministic():
    seed = _seed()
    rng = random.Random(0)
    chain = [("weaken_compare", "truthy"), ("skip_unit", "mark_skip")]
    a = apply_chain(seed, tamper_ops.OPS, chain, "det", 7)
    b = apply_chain(seed, tamper_ops.OPS, chain, "det", 7)
    assert a is not None and b is not None
    assert a.tests == b.tests and a.extras == b.extras
    del rng
