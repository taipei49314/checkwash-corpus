"""Tampering operators — the rule-space arm.

Each operator is one THREATMODEL family with several surface spellings. The
spelling table is the point: the 2026-09-01 history was one spelling patched
at a time (except, then raises, then suppress, then the tuple), so a fuzzer
that draws spellings from a table is the mechanical version of "did you close
the family or the instance". An operator returns None when the seed has no
site of the required shape; nothing here decides whether the result is a
wash — pytest does.
"""

from __future__ import annotations

import ast

from corpus.stress import edits as E
from corpus.stress.common import (
    Variant, add_ini_option, append_extra, assert_body_lines, eq_parts,
    pick_assert, pick_test, set_extra, set_source, uses_self,
)
from corpus.stress.seeds import Seed


def _indent(lines: list[str]) -> list[str]:
    return ["    " + line if line.strip() else "" for line in lines]


# ---------------------------------------------------------------- assertion level

def weaken_compare(v: Variant, seed: Seed, sp: str, rng) -> Variant | None:
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None:
        return None
    lhs, rhs, _l, _r = parts
    forms = {
        "is_not_none": f"assert {lhs} is not None",
        "truthy": f"assert {lhs}",
        "ge_zero": f"assert {lhs} >= 0",
        "ne_none": f"assert {lhs} != None",
        "isinstance_of_expected": f"assert isinstance({lhs}, type({rhs}))",
        "in_pair": f"assert {lhs} in ({rhs}, {lhs})",
        "len_ge_zero": f"assert len(str({lhs})) >= 0",
    }
    return set_source(v, seed, E.replace_stmt(t.src, t.node, [forms[sp]]))


def tautology(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None:
        return None
    lhs, rhs, _l, _r = parts
    forms = {
        "lhs_eq_lhs": f"assert {lhs} == {lhs}",
        "rhs_eq_rhs": f"assert {rhs} == {rhs}",
        "or_true": f"assert {lhs} == {rhs} or True",
        "or_self": f"assert {lhs} == {rhs} or {lhs} == {lhs}",
        "is_lhs": f"assert {lhs} is {lhs}",
    }
    return set_source(v, seed, E.replace_stmt(t.src, t.node, [forms[sp]]))


def delete_assert(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    test_expr = E.paren(E.seg(t.src, t.node.test))
    if sp == "remove":
        return set_source(v, seed, E.delete_stmt(t.src, t.node, t.block))
    if sp == "pass":
        return set_source(v, seed, E.replace_stmt(t.src, t.node, ["pass"]))
    if sp == "call_only":
        expr = parts[0] if parts else test_expr
        return set_source(v, seed, E.replace_stmt(t.src, t.node, [expr]))
    if sp == "bind_result":
        expr = parts[0] if parts else test_expr
        return set_source(v, seed, E.replace_stmt(t.src, t.node, [f"_ = {expr}"]))
    if sp == "print_result":
        expr = parts[0] if parts else test_expr
        return set_source(v, seed, E.replace_stmt(t.src, t.node, [f"print({expr})"]))
    return None


_NEUTRALISERS = {
    "raises_assertionerror": ("with pytest.raises(AssertionError):", ("import pytest",), False),
    "raises_exception": ("with pytest.raises(Exception):", ("import pytest",), False),
    "raises_baseexception": ("with pytest.raises(BaseException):", ("import pytest",), False),
    "raises_bare_import": ("with raises(AssertionError):", ("from pytest import raises",), False),
    "raises_tuple": ("with pytest.raises((ValueError, AssertionError)):", ("import pytest",), False),
    "suppress_assertionerror": ("with contextlib.suppress(AssertionError):", ("import contextlib",), False),
    "suppress_bare_exception": ("with suppress(Exception):", ("from contextlib import suppress",), False),
    "suppress_alias": ("with s(AssertionError):", ("from contextlib import suppress as s",), False),
    "assertraises_self": ("with self.assertRaises(AssertionError):", (), True),
    "assertraisesregex_self": ('with self.assertRaisesRegex(AssertionError, ".*"):', (), True),
    "aliased_value": ("with pytest.raises(_E):", ("import pytest",), False),
    "dynamic_callee": ("with _r(AssertionError):", ("import pytest",), False),
}

_EXCEPT_SPELLINGS = {
    "except_assertionerror_pass": "except AssertionError:",
    "except_exception_pass": "except Exception:",
    "except_bare_pass": "except:",
    "except_tuple_pass": "except (ValueError, AssertionError):",
    "except_baseexception_pass": "except BaseException:",
    "except_assertionerror_return": "except AssertionError:",
}


def neutralize_context(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    body = assert_body_lines(t)
    if sp in _NEUTRALISERS:
        header, imports, needs_self = _NEUTRALISERS[sp]
        if needs_self and not uses_self(t):
            return None
        src = E.replace_stmt(t.src, t.node, [header] + _indent(body))
        if sp == "aliased_value":
            tree = E.parse(src)
            if tree is None:
                return None
            src = E.insert_after_imports(src, tree, ["_E = AssertionError"])
        if sp == "dynamic_callee":
            tree = E.parse(src)
            if tree is None:
                return None
            src = E.insert_after_imports(src, tree, ["_r = pytest.raises"])
        return set_source(v, seed, src, imports)
    if sp in _EXCEPT_SPELLINGS:
        handler = _EXCEPT_SPELLINGS[sp]
        tail = ["    return"] if sp.endswith("_return") else ["    pass"]
        src = E.replace_stmt(t.src, t.node, ["try:"] + _indent(body) + [handler] + tail)
        return set_source(v, seed, src)
    return None


_DEAD_BRANCHES = {
    "if_false": ("if False:", ()),
    "if_zero": ("if 0:", ()),
    "if_none": ("if None:", ()),
    "if_empty_str": ('if "":', ()),
    "platform_unknown": ('if sys.platform == "unknown-os":', ("import sys",)),
    "version_far": ("if sys.version_info >= (99, 0):", ("import sys",)),
    "env_never_set": ('if os.environ.get("CHECKWASH_STRESS_NEVER_SET"):', ("import os",)),
    "len_empty": ("if len([]):", ()),
    "while_false": ("while False:", ()),
}


def dead_branch(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    header, imports = _DEAD_BRANCHES[sp]
    src = E.replace_stmt(t.src, t.node, [header] + _indent(assert_body_lines(t)))
    return set_source(v, seed, src, imports)


def tolerance_loosen(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None or not E.is_number(parts[3]):
        return None
    lhs, rhs, _l, _r = parts
    forms = {
        "approx_rel_one": (f"assert {lhs} == pytest.approx({rhs}, rel=1.0)", ("import pytest",)),
        "approx_abs_huge": (f"assert {lhs} == pytest.approx({rhs}, abs=1e9)", ("import pytest",)),
        "isclose_rel_one": (f"assert math.isclose({lhs}, {rhs}, rel_tol=1.0)", ("import math",)),
        "abs_diff_huge": (f"assert abs({lhs} - {rhs}) < 1e9", ()),
    }
    text, imports = forms[sp]
    return set_source(v, seed, E.replace_stmt(t.src, t.node, [text]), imports)


def subject_normalize(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None:
        return None
    lhs, rhs, _l, _r = parts
    forms = {
        "bool_both": f"assert bool({lhs}) == bool({rhs})",
        "type_both": f"assert type({lhs}) == type({rhs})",
        "str_empty_prefix": f"assert str({lhs})[:0] == str({rhs})[:0]",
        "repr_len_sign": f"assert (len(repr({lhs})) > 0) == (len(repr({rhs})) > 0)",
    }
    return set_source(v, seed, E.replace_stmt(t.src, t.node, [forms[sp]]))


def disguised_extract_weaken(v, seed, sp, rng):
    """Faithful-looking extraction whose helper body is weaker (the disguised arm)."""
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None:
        return None
    lhs, rhs, _l, _r = parts
    helper = "_check_result"
    if helper in t.src:
        return None
    bodies = {
        "helper_truthy": "assert actual",
        "helper_is_not_none": "assert actual is not None",
        "helper_type_only": "assert type(actual) == type(expected)",
        "helper_len_ge_zero": "assert len(str(actual)) >= 0",
        "helper_or_true": "assert actual == expected or True",
    }
    src = E.replace_stmt(t.src, t.node, [f"{helper}({lhs}, {rhs})"])
    src = E.append_module(src, [f"def {helper}(actual, expected):", f"    {bodies[sp]}"])
    return set_source(v, seed, src)


def uncalled_helper(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    body = assert_body_lines(t)
    if sp == "nested_def":
        src = E.replace_stmt(t.src, t.node, ["def _check():"] + _indent(body))
    elif sp == "lambda":
        src = E.replace_stmt(t.src, t.node, [f"_check = lambda: {E.paren(E.seg(t.src, t.node.test))}"])
    elif sp == "module_helper":
        src = E.delete_stmt(t.src, t.node, t.block)
        src = E.append_module(src, ["def _verify_result():"] + _indent(body))
    elif sp == "callable_check":
        src = E.replace_stmt(t.src, t.node, ["def _check():"] + _indent(body) + ["assert callable(_check)"])
    else:
        return None
    return set_source(v, seed, src)


# ---------------------------------------------------------------- unit level

_DECORATORS = {
    "mark_skip": ("@pytest.mark.skip", ("import pytest",)),
    "mark_skip_reason": ('@pytest.mark.skip(reason="flaky on CI")', ("import pytest",)),
    "mark_xfail": ("@pytest.mark.xfail", ("import pytest",)),
    "mark_xfail_nonstrict": ('@pytest.mark.xfail(strict=False, reason="known issue")', ("import pytest",)),
    "skipif_true": ('@pytest.mark.skipif(True, reason="temporarily disabled")', ("import pytest",)),
    "skipif_platform": ('@pytest.mark.skipif(sys.platform != "unknown-os", reason="needs unknown-os")', ("import pytest", "import sys")),
    "unittest_skip": ('@unittest.skip("temporarily disabled")', ("import unittest",)),
    "skipif_env": ('@pytest.mark.skipif(not os.environ.get("RUN_SLOW_TESTS"), reason="slow")', ("import pytest", "import os")),
}

_BODY_SKIPS = {
    "body_skip": ('pytest.skip("skipping")', ("import pytest",)),
    "body_xfail": ('pytest.xfail("known failure")', ("import pytest",)),
    "body_importorskip": ('pytest.importorskip("module_that_does_not_exist_zzz")', ("import pytest",)),
}


def skip_unit(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None:
        return None
    if sp in _DECORATORS:
        text, imports = _DECORATORS[sp]
        return set_source(v, seed, E.insert_decorator(s.src, s.func, text), imports)
    if sp in _BODY_SKIPS:
        text, imports = _BODY_SKIPS[sp]
        return set_source(v, seed, E.insert_first_statement(s.src, s.func, [text]), imports)
    return None


def early_return(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None:
        return None
    forms = {
        "return": ["return"],
        "return_todo": ["return  # TODO: re-enable once fixed"],
        "if_true_return": ["if True:", "    return"],
        "return_none": ["return None"],
    }
    return set_source(v, seed, E.insert_first_statement(s.src, s.func, forms[sp]))


def parametrize_empty(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None:
        return None
    forms = {
        "empty_list": '@pytest.mark.parametrize("_unused", [])',
        "empty_tuple": '@pytest.mark.parametrize("_unused", ())',
        "list_call": '@pytest.mark.parametrize("_unused", list())',
        "filtered_empty": '@pytest.mark.parametrize("_unused", [x for x in [] if x])',
    }
    src = E.edit_def_line(s.src, s.func, lambda line: E.add_first_param(line, "_unused"))
    tree = E.parse(src)
    if tree is None:
        return None
    # relocate the function node after the signature edit (same line numbers)
    func = next((f for f, _c in E.test_functions(tree) if f.lineno == s.func.lineno), None)
    if func is None:
        return None
    src = E.insert_decorator(src, func, forms[sp])
    return set_source(v, seed, src, ("import pytest",))


def rename_nontest(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None:
        return None
    name = s.func.name
    new = {
        "check_prefix": "check_" + name[len("test_"):] if name.startswith("test_") else "check" + name[4:],
        "underscore_prefix": "_" + name,
        "x_prefix": "x" + name,
        "typo": "tset" + name[4:],
    }[sp]
    src = E.edit_def_line(s.src, s.func, lambda line: line.replace(f"def {name}(", f"def {new}(", 1))
    return set_source(v, seed, src)


def async_convert(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None or isinstance(s.func, ast.AsyncFunctionDef):
        return None
    src = E.edit_def_line(s.src, s.func, lambda line: line.replace("def ", "async def ", 1))
    return set_source(v, seed, src)


# ---------------------------------------------------------------- module level

def module_rebind(v, seed, sp, rng):
    """A module-level stand-in for the symbol under test (REPRO-PACK B1 family)."""
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None:
        return None
    _lhs, rhs, lhs_node, rhs_node = parts
    name = E.call_name(lhs_node)
    if name is None or not E.is_literal(rhs_node):
        return None
    found = E.import_of(t.tree, name)
    if found is None:
        return None
    module, import_line = found
    alias = module.replace(".", "_")
    if sp == "lambda_rebind":
        src = E.insert_after_imports(t.src, t.tree, [f"{name} = lambda *args, **kwargs: {rhs}  # legacy stub"])
    elif sp == "def_rebind":
        src = E.insert_after_imports(t.src, t.tree, [f"def {name}(*args, **kwargs):", f"    return {rhs}"])
    elif sp == "attr_patch_before_import":
        src = E.insert_before(t.src, import_line, [f"import {module} as _real_{alias}", f"_real_{alias}.{name} = lambda *args, **kwargs: {rhs}"])
    elif sp == "sys_modules_swap":
        src = E.insert_before(t.src, import_line, [
            "import sys", "import types",
            f'_fake_{alias} = types.ModuleType("{module}")',
            f"_fake_{alias}.{name} = lambda *args, **kwargs: {rhs}",
            f'sys.modules["{module}"] = _fake_{alias}',
        ])
    elif sp == "conftest_configure_swap":
        snippet = "\n".join([
            "import sys", "import types", "",
            "def pytest_configure(config):",
            f'    _fake = types.ModuleType("{module}")',
            f"    _fake.{name} = lambda *args, **kwargs: {rhs}",
            f'    sys.modules["{module}"] = _fake',
        ]) + "\n"
        return append_extra(v, "tests/conftest.py", snippet)
    else:
        return None
    return set_source(v, seed, src)


def conftest_ignore(v, seed, sp, rng):
    basename = seed.main_test.rsplit("/", 1)[-1]
    stem = basename[:-3]
    forms = {
        "collect_ignore": f'collect_ignore = ["{basename}"]\n',
        "collect_ignore_glob": f'collect_ignore_glob = ["{stem}*.py"]\n',
        "pytest_ignore_collect": "\n".join([
            "def pytest_ignore_collect(collection_path, config):",
            f'    return collection_path.name == "{basename}"',
        ]) + "\n",
        "collection_modifyitems_skip": "\n".join([
            "import pytest", "",
            "def pytest_collection_modifyitems(config, items):",
            "    for item in items:",
            f'        if "{stem}" in str(item.fspath):',
            '            item.add_marker(pytest.mark.skip(reason="quarantined"))',
        ]) + "\n",
    }
    return append_extra(v, "tests/conftest.py", forms[sp])


def addopts(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None:
        return None
    name = s.func.name
    ini = v.extras.get("pytest.ini", "")
    if sp == "collect_only":
        return set_extra(v, "pytest.ini", add_ini_option(ini, "addopts", "--collect-only"))
    if sp == "co_short":
        return set_extra(v, "pytest.ini", add_ini_option(ini, "addopts", "--co"))
    if sp == "k_not_name":
        return set_extra(v, "pytest.ini", add_ini_option(ini, "addopts", f'-k "not {name}"'))
    if sp == "deselect":
        return set_extra(v, "pytest.ini", add_ini_option(ini, "addopts", f"--deselect {seed.main_test}::{name}"))
    if sp == "ignore_file":
        return set_extra(v, "pytest.ini", add_ini_option(ini, "addopts", f"--ignore={seed.main_test}"))
    if sp == "m_not_slow_with_marker":
        nv = set_source(v, seed, E.insert_decorator(s.src, s.func, "@pytest.mark.slow"), ("import pytest",))
        if nv is None:
            return None
        return set_extra(nv, "pytest.ini", add_ini_option(nv.extras.get("pytest.ini", ""), "addopts", '-m "not slow"'))
    if sp == "python_files_none":
        return set_extra(v, "pytest.ini", add_ini_option(ini, "python_files", "nothing_*.py"))
    if sp == "testpaths_elsewhere":
        return set_extra(v, "pytest.ini", add_ini_option(ini, "testpaths", "docs"))
    if sp == "exit_zero_plugin":
        # `-p no:` on a plugin that does not exist is a usage error; a real
        # runner-mode flip is `--collect-only`. Kept as a negative probe.
        return set_extra(v, "pytest.ini", add_ini_option(ini, "addopts", "-p no:warnings"))
    return None


OPS = {
    "weaken_compare": ("assertion", tuple(["is_not_none", "truthy", "ge_zero", "ne_none", "isinstance_of_expected", "in_pair", "len_ge_zero"]), weaken_compare),
    "tautology": ("assertion", ("lhs_eq_lhs", "rhs_eq_rhs", "or_true", "or_self", "is_lhs"), tautology),
    "delete_assert": ("assertion", ("remove", "pass", "call_only", "bind_result", "print_result"), delete_assert),
    "neutralize_context": ("assertion", tuple(list(_NEUTRALISERS) + list(_EXCEPT_SPELLINGS)), neutralize_context),
    "dead_branch": ("assertion", tuple(_DEAD_BRANCHES), dead_branch),
    "tolerance_loosen": ("assertion", ("approx_rel_one", "approx_abs_huge", "isclose_rel_one", "abs_diff_huge"), tolerance_loosen),
    "subject_normalize": ("assertion", ("bool_both", "type_both", "str_empty_prefix", "repr_len_sign"), subject_normalize),
    "disguised_extract_weaken": ("assertion", ("helper_truthy", "helper_is_not_none", "helper_type_only", "helper_len_ge_zero", "helper_or_true"), disguised_extract_weaken),
    "uncalled_helper": ("assertion", ("nested_def", "lambda", "module_helper", "callable_check"), uncalled_helper),
    "skip_unit": ("unit", tuple(list(_DECORATORS) + list(_BODY_SKIPS)), skip_unit),
    "early_return": ("unit", ("return", "return_todo", "if_true_return", "return_none"), early_return),
    "parametrize_empty": ("unit", ("empty_list", "empty_tuple", "list_call", "filtered_empty"), parametrize_empty),
    "rename_nontest": ("unit", ("check_prefix", "underscore_prefix", "x_prefix", "typo"), rename_nontest),
    "async_convert": ("unit", ("async_def",), async_convert),
    "module_rebind": ("module", ("lambda_rebind", "def_rebind", "attr_patch_before_import", "sys_modules_swap", "conftest_configure_swap"), module_rebind),
    "conftest_ignore": ("collection", ("collect_ignore", "collect_ignore_glob", "pytest_ignore_collect", "collection_modifyitems_skip"), conftest_ignore),
    "addopts": ("config", ("collect_only", "co_short", "k_not_name", "deselect", "ignore_file", "m_not_slow_with_marker", "python_files_none", "testpaths_elsewhere", "exit_zero_plugin"), addopts),
}
