"""Open-ended edits and robustness inputs.

`random_edit` is the discovery arm: small random AST-anchored edits with no
taxonomy behind them. Most break the suite or change nothing; the oracle
throws those away. The survivors — random edits that make a red suite green
on unchanged buggy production — are exactly the tampering shapes nobody
named, and any that pass the engine are reported separately from the
rule-space arm so the two numbers are never averaged.

`robust_inputs` needs no oracle: malformed, pathological and oversized inputs
that must not crash the engine, must judge deterministically, and must stay
inside the perf budget.
"""

from __future__ import annotations

import ast

from corpus.stress import edits as E
from corpus.stress.common import Variant, add_ini_option, append_extra, pick_test, set_extra, set_source
from corpus.stress.seeds import Seed

_LITERALS = ["0", "1", "-1", '""', '"x"', "None", "True", "False", "[]", "{}", "0.0"]
_CONDS = ["True", "False", "1", "0", '""', "None", "not None", "len([])", "[] == []", "0.0", "-1"]
_DECOS = [
    ("@pytest.mark.skip", "import pytest"),
    ("@pytest.mark.xfail", "import pytest"),
    ('@pytest.mark.parametrize("_", [])', "import pytest"),
    ('@pytest.mark.skipif(True, reason="x")', "import pytest"),
    ("@pytest.mark.slow", "import pytest"),
    ('@unittest.skip("x")', "import unittest"),
    ("@staticmethod", None),
    ("@property", None),
    ("@functools.lru_cache", "import functools"),
]
_IMPORTS = ["import os", "import sys", "import unittest.mock", "import contextlib", "import pytest", "from unittest import mock", "import warnings"]
_STATEMENTS = [
    ["pass"],
    ['pytest.skip("x")'],
    ["return"],
    ["raise SystemExit(0)"],
    ['warnings.warn("x")'],
    ["_ = None"],
    ["if True:", "    return"],
    ["assert True"],
    ["assert 1"],
]
_INI_LINES = [
    ("addopts", "--collect-only"),
    ("addopts", "-x"),
    ("addopts", "-q"),
    ("addopts", '-k "not test"'),
    ("addopts", "-p no:warnings"),
    ("addopts", "--maxfail=1"),
    ("addopts", "--deselect tests"),
    ("testpaths", "."),
    ("testpaths", "src"),
    ("python_files", "*.py"),
    ("python_files", "check_*.py"),
    ("python_functions", "check_*"),
    ("python_classes", "Check*"),
    ("norecursedirs", "tests"),
    ("markers", "slow: slow"),
    ("filterwarnings", "error"),
    ("xfail_strict", "true"),
]
_CONFTEST = [
    'collect_ignore = ["test_zz_padding.py"]\n',
    "import pytest\n\n@pytest.fixture(autouse=True)\ndef _quiet():\n    yield\n",
    "def pytest_collection_modifyitems(config, items):\n    items[:] = items[:1]\n",
    "def pytest_collection_modifyitems(config, items):\n    items.reverse()\n",
    "import pytest\n\ndef pytest_runtest_setup(item):\n    pytest.skip('x')\n",
    "def pytest_sessionstart(session):\n    pass\n",
    "import sys\nsys.dont_write_bytecode = True\n",
    "def pytest_runtest_makereport(item, call):\n    pass\n",
]


def _pick_stmt(s, rng):
    body = E.body_statements(s.func)
    return rng.choice(body) if body else None


def random_edit(v: Variant, seed: Seed, sp: str, rng) -> Variant | None:
    s = pick_test(v, seed, rng)
    if s is None:
        return None
    src = s.src
    if sp == "delete_statement":
        st = _pick_stmt(s, rng)
        return None if st is None else set_source(v, seed, E.delete_stmt(src, st, E.parent_block(s.func, st)))
    if sp == "duplicate_statement":
        st = _pick_stmt(s, rng)
        if st is None:
            return None
        return set_source(v, seed, E.insert_before(src, st.end_lineno + 1, E.stmt_lines(src, st), E.indent_at(src, st.lineno)))
    if sp == "swap_compare_op":
        cmps = [n for n in ast.walk(s.func) if isinstance(n, ast.Compare) and len(n.ops) == 1]
        if not cmps:
            return None
        node = rng.choice(cmps)
        swaps = {ast.Eq: "!=", ast.NotEq: "==", ast.Lt: "<=", ast.LtE: "<", ast.Gt: ">=", ast.GtE: ">", ast.In: "not in", ast.NotIn: "in", ast.Is: "is not", ast.IsNot: "is"}
        op = swaps.get(type(node.ops[0]))
        if op is None:
            return None
        text = f"{E.seg(src, node.left)} {op} {E.seg(src, node.comparators[0])}"
        out = E.replace_expr(src, node, text)
        return None if out is None else set_source(v, seed, out)
    if sp == "replace_literal":
        consts = [n for n in ast.walk(s.func) if isinstance(n, ast.Constant) and not isinstance(n.value, (bytes,)) and n.lineno == n.end_lineno]
        consts = [n for n in consts if not (isinstance(n.value, str) and len(n.value) > 40)]
        if not consts:
            return None
        node = rng.choice(consts)
        out = E.replace_expr(src, node, rng.choice(_LITERALS))
        return None if out is None else set_source(v, seed, out)
    if sp == "wrap_if":
        st = _pick_stmt(s, rng)
        if st is None:
            return None
        cond = rng.choice(_CONDS)
        lines = [f"if {cond}:"] + ["    " + l if l.strip() else "" for l in E.stmt_lines(src, st)]
        return set_source(v, seed, E.replace_stmt(src, st, lines))
    if sp == "insert_return":
        st = _pick_stmt(s, rng)
        if st is None:
            return None
        return set_source(v, seed, E.insert_before(src, st.lineno, ["return"], E.indent_at(src, st.lineno)))
    if sp == "rename_identifier":
        eligible = [f for f, _c in E.test_functions(s.tree) if len(E.names_used(f)) >= 2]
        if not eligible:
            return None
        func = rng.choice(eligible)
        old, new = rng.sample(sorted(E.names_used(func)), 2)
        return set_source(v, seed, E.rename_in_range(src, func.lineno, func.end_lineno, old, new))
    if sp == "add_decorator":
        deco, imp = rng.choice(_DECOS)
        return set_source(v, seed, E.insert_decorator(src, s.func, deco), (imp,) if imp else ())
    if sp == "add_import":
        return set_source(v, seed, E.ensure_import(src, rng.choice(_IMPORTS)))
    if sp == "name_to_literal":
        names = [n for n in ast.walk(s.func) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.lineno == n.end_lineno]
        if not names:
            return None
        out = E.replace_expr(src, rng.choice(names), rng.choice(_LITERALS))
        return None if out is None else set_source(v, seed, out)
    if sp == "edit_call_args":
        calls = [n for n in ast.walk(s.func) if isinstance(n, ast.Call) and n.lineno == n.end_lineno]
        if not calls:
            return None
        node = rng.choice(calls)
        args = [E.seg(src, a) for a in node.args]
        if rng.random() < 0.5 and args:
            args = args[:-1]
        else:
            args = args + [rng.choice(_LITERALS)]
        kw = [f"{k.arg}={E.seg(src, k.value)}" if k.arg else f"**{E.seg(src, k.value)}" for k in node.keywords]
        text = f"{E.seg(src, node.func)}({', '.join(args + kw)})"
        out = E.replace_expr(src, node, text)
        return None if out is None else set_source(v, seed, out)
    if sp == "assert_test_replace":
        asserts = E.direct_asserts(s.func)
        if not asserts:
            return None
        node = rng.choice(asserts)
        choice = rng.choice(["True", "not False", "1", f"{E.paren(E.seg(src, node.test))} or True", "[] == []", "None is None"])
        return set_source(v, seed, E.replace_stmt(src, node, [f"assert {choice}"]))
    if sp == "move_statement":
        body = E.body_statements(s.func)
        if len(body) < 2:
            return None
        i = rng.randrange(len(body) - 1)
        a, b = body[i], body[i + 1]
        la, lb = E.stmt_lines(src, a), E.stmt_lines(src, b)
        indent = E.indent_at(src, a.lineno)
        lines = E.lines_of(src)
        new = [(indent + l) if l.strip() else "" for l in lb + la]
        return set_source(v, seed, "\n".join(lines[: a.lineno - 1] + new + lines[b.end_lineno :]))
    if sp == "insert_statement":
        st = _pick_stmt(s, rng)
        if st is None:
            return None
        stmt = rng.choice(_STATEMENTS)
        imports = ("import pytest",) if "pytest." in stmt[0] else (("import warnings",) if "warnings." in stmt[0] else ())
        return set_source(v, seed, E.insert_before(src, st.lineno, stmt, E.indent_at(src, st.lineno)), imports)
    if sp == "config_line":
        key, value = rng.choice(_INI_LINES)
        return set_extra(v, "pytest.ini", add_ini_option(v.extras.get("pytest.ini", ""), key, value))
    if sp == "conftest_snippet":
        return append_extra(v, "tests/conftest.py", rng.choice(_CONFTEST))
    if sp == "rename_test":
        name = s.func.name
        new = rng.choice([f"{name}_v2", f"check_{name}", f"{name}2", "test_" + name])
        return set_source(v, seed, E.edit_def_line(src, s.func, lambda line: line.replace(f"def {name}(", f"def {new}(", 1)))
    return None


RANDOM_SPELLINGS = (
    "delete_statement", "duplicate_statement", "swap_compare_op", "replace_literal", "wrap_if",
    "insert_return", "rename_identifier", "add_decorator", "add_import", "name_to_literal",
    "edit_call_args", "assert_test_replace", "move_statement", "insert_statement", "config_line",
    "conftest_snippet", "rename_test",
)

OPS = {"random_edit": ("open", RANDOM_SPELLINGS, random_edit)}


# ---------------------------------------------------------------- robustness inputs

ROBUST_SPELLINGS = (
    "syntax_error", "bom_prefix", "crlf", "tabs", "unicode_identifier", "nul_byte", "latin1_bytes",
    "giant_asserts", "deep_nesting", "long_line", "empty_file", "comments_only", "mega_diff_300",
    "noop_diff", "delete_test_file", "binary_test_file", "mixed_newlines", "nested_parens",
)


def robust_inputs(seed: Seed, sp: str, rng) -> tuple[dict[str, str | bytes | None], dict[str, str]]:
    """(after-side test files, extras) for one pathological shape."""
    main = seed.main_test
    src = seed.main_source()
    tests: dict[str, str | bytes | None] = {}
    extras = dict(seed.extras)
    if sp == "syntax_error":
        tests[main] = src.rstrip("\n") + "\n\ndef test_broken(:\n    assert 1\n"
    elif sp == "bom_prefix":
        tests[main] = ("﻿" + src).encode("utf-8")
    elif sp == "crlf":
        tests[main] = src.replace("\n", "\r\n")
    elif sp == "tabs":
        tests[main] = src.replace("    ", "\t")
    elif sp == "unicode_identifier":
        tests[main] = src.rstrip("\n") + "\n\ndef test_測試_ünïcode():\n    值 = 1\n    assert 值 == 1\n"
    elif sp == "nul_byte":
        tests[main] = src.encode("utf-8") + b"\n# \x00 nul\n"
    elif sp == "latin1_bytes":
        tests[main] = src.encode("utf-8") + "\n# caf\xe9\n".encode("latin-1")
    elif sp == "giant_asserts":
        tests[main] = src.rstrip("\n") + "\n\ndef test_giant():\n" + "".join(f"    assert {i} == {i}\n" for i in range(4000))
    elif sp == "deep_nesting":
        body = "".join(("    " * (i + 1)) + "if True:\n" for i in range(150)) + ("    " * 151) + "assert 1 == 1\n"
        tests[main] = src.rstrip("\n") + "\n\ndef test_deep():\n" + body
    elif sp == "long_line":
        tests[main] = src.rstrip("\n") + '\n\ndef test_long():\n    assert "' + ("x" * 30000) + '" != ""\n'
    elif sp == "empty_file":
        tests[main] = ""
    elif sp == "comments_only":
        tests[main] = "# nothing here\n# still nothing\n"
    elif sp == "mega_diff_300":
        for i in range(300):
            tests[f"tests/generated/test_gen_{i:03d}.py"] = src.replace("def test_", f"def test_g{i}_")
    elif sp == "noop_diff":
        tests[main] = src
    elif sp == "delete_test_file":
        tests[main] = None
    elif sp == "binary_test_file":
        tests["tests/test_blob.py"] = bytes(range(256)) * 16
    elif sp == "mixed_newlines":
        lines = src.split("\n")
        tests[main] = "".join(line + ("\r\n" if i % 2 else "\n") for i, line in enumerate(lines))
    elif sp == "nested_parens":
        tests[main] = src.rstrip("\n") + "\n\ndef test_parens():\n    assert " + ("(" * 190) + "1" + (")" * 190) + " == 1\n"
    return tests, extras
