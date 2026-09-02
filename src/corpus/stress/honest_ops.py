"""Honest operators — semantics-preserving test refactors that must stay silent.

A block on one of these is a false positive by the refactor corpus's
construction: both sides still catch the bug (pytest red on buggy production,
green on correct production), so nothing was weakened. The oracle enforces
that; an operator whose output stops catching the bug is discarded, not
counted against the engine.
"""

from __future__ import annotations

import ast

from corpus.stress import edits as E
from corpus.stress.common import Variant, camel, eq_parts, pick_assert, pick_test, set_source
from corpus.stress.seeds import Seed


def _indent(lines: list[str], n: int = 4) -> list[str]:
    return [(" " * n + line) if line.strip() else "" for line in lines]


def rename_local(v: Variant, seed: Seed, sp: str, rng) -> Variant | None:
    s = pick_test(v, seed, rng)
    if s is None:
        return None
    names = E.local_names(s.func)
    if not names:
        return None
    old = rng.choice(names)
    new = {"suffix_value": f"{old}_value", "actual": "actual", "result": "result", "got": "got"}[sp]
    if new == old or new in E.names_used(s.func):
        return None
    src = E.rename_in_range(s.src, s.func.lineno, s.func.end_lineno, old, new)
    return set_source(v, seed, src)


def docstring_comment(v, seed, sp, rng):
    if sp == "docstring":
        s = pick_test(v, seed, rng)
        if s is None:
            return None
        return set_source(v, seed, E.insert_first_statement(s.src, s.func, ['"""Regression test; expected values verified by hand."""']))
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    if sp == "comment_above_assert":
        src = E.insert_before(t.src, t.node.lineno, ["# expected value verified against the specification"], E.indent_at(t.src, t.node.lineno))
        return set_source(v, seed, src)
    if sp == "blank_line_above_assert":
        src = E.insert_before(t.src, t.node.lineno, [""])
        return set_source(v, seed, src)
    return None


def extract_faithful(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None:
        return None
    lhs, rhs, _l, _r = parts
    helper = {"positional": "_check_result", "keyword": "_check_result", "assert_equal": "assert_equal"}[sp]
    if f"def {helper}(" in t.src:
        return None
    call = f"{helper}(actual={lhs}, expected={rhs})" if sp == "keyword" else f"{helper}({lhs}, {rhs})"
    src = E.replace_stmt(t.src, t.node, [call])
    src = E.append_module(src, [f"def {helper}(actual, expected):", "    assert actual == expected"])
    return set_source(v, seed, src)


def split_test(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None or s.cls is not None or s.func.decorator_list:
        return None
    body = E.body_statements(s.func)
    asserts = [st for st in body if isinstance(st, ast.Assert)]
    if len(asserts) < 2:
        return None
    moved = asserts[-1]
    keep = [st for st in body if not isinstance(st, ast.Assert)]
    new_name = f"{s.func.name}_{'part2' if sp == 'part2' else 'tail'}"
    lines = [f"def {new_name}():"]
    for st in keep + [moved]:
        lines.extend(_indent(E.stmt_lines(s.src, st)))
    if len(lines) == 1:
        lines.append("    pass")
    src = E.delete_stmt(s.src, moved, E.parent_block(s.func, moved))
    src = E.append_module(src, lines)
    return set_source(v, seed, src)


def merge_tests(v, seed, sp, rng):
    src = v.tests[seed.main_test]
    tree = E.parse(src)
    if tree is None:
        return None
    funcs = [f for f, c in E.test_functions(tree) if c is None and not f.decorator_list and isinstance(f, ast.FunctionDef)]
    if len(funcs) < 2:
        return None
    first, second = funcs[0], funcs[1]
    second_lines = []
    for st in E.body_statements(second):
        second_lines.extend(E.stmt_lines(src, st))
    if not second_lines:
        return None
    lines = E.lines_of(src)
    # remove the second function first (later in the file), then extend the first
    del lines[second.lineno - 1 : second.end_lineno]
    # drop blank lines left immediately above the removed function
    while second.lineno - 2 >= 0 and second.lineno - 2 < len(lines) and not lines[second.lineno - 2].strip() and lines[second.lineno - 2 - 1 : second.lineno - 2] == [""]:
        del lines[second.lineno - 2]
    src = "\n".join(lines)
    tree = E.parse(src)
    if tree is None:
        return None
    first = next((f for f, _c in E.test_functions(tree) if f.name == first.name), None)
    if first is None:
        return None
    indent = E.indent_at(src, E.body_insert_point(first))
    insert_at = (first.end_lineno or first.lineno) + 1
    src = E.insert_before(src, insert_at, second_lines, indent)
    return set_source(v, seed, src)


def approx_exact(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None:
        return None
    _lhs, rhs, _l, rhs_node = parts
    if not (isinstance(rhs_node, ast.Constant) and isinstance(rhs_node.value, float)):
        return None
    text = {"approx_default": f"pytest.approx({rhs})", "approx_tight": f"pytest.approx({rhs}, rel=1e-9)"}[sp]
    src = E.replace_expr(t.src, rhs_node, text)
    if src is None:
        return None
    return set_source(v, seed, src, ("import pytest",))


def parametrize_single(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None or s.cls is not None or s.func.decorator_list:
        return None
    body = E.body_statements(s.func)
    if len(body) != 1 or not isinstance(body[0], ast.Assert):
        return None
    node = body[0]
    cmp = E.eq_compare(node)
    if cmp is None:
        return None
    lhs, rhs = cmp
    if not (isinstance(lhs, ast.Call) and isinstance(lhs.func, ast.Name) and len(lhs.args) == 1 and not lhs.keywords):
        return None
    if not (E.is_literal(lhs.args[0]) and E.is_literal(rhs)):
        return None
    fn = lhs.func.id
    arg, expected = E.seg(s.src, lhs.args[0]), E.seg(s.src, rhs)
    if "\n" in arg or "\n" in expected:
        return None
    names = {"arg_expected": ("arg", "expected"), "value_want": ("value", "want")}[sp]
    src = E.replace_stmt(s.src, node, [f"assert {fn}({names[0]}) == {names[1]}"])
    src = E.edit_def_line(src, s.func, lambda line: E.add_first_param(E.add_first_param(line, names[1]), names[0]))
    tree = E.parse(src)
    if tree is None:
        return None
    func = next((f for f, _c in E.test_functions(tree) if f.lineno == s.func.lineno), None)
    if func is None:
        return None
    src = E.insert_decorator(src, func, f'@pytest.mark.parametrize("{names[0]}, {names[1]}", [({arg}, {expected})])')
    return set_source(v, seed, src, ("import pytest",))


def to_unittest(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None or s.cls is not None or s.func.decorator_list or not isinstance(s.func, ast.FunctionDef):
        return None
    body = E.body_statements(s.func)
    if not body or any(isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.With, ast.For, ast.While, ast.If, ast.Try)) for st in body):
        return None
    lines = [f"class Test{camel(s.func.name)}(unittest.TestCase):", f"    def {s.func.name}(self):"]
    for st in body:
        if isinstance(st, ast.Assert):
            cmp = E.eq_compare(st)
            if cmp is not None:
                lhs, rhs = E.paren(E.seg(s.src, cmp[0])), E.paren(E.seg(s.src, cmp[1]))
                method = {"assertEqual": "assertEqual", "assertTrue": "assertTrue"}[sp]
                if method == "assertEqual":
                    lines.append(f"        self.assertEqual({lhs}, {rhs})")
                else:
                    lines.append(f"        self.assertTrue({lhs} == {rhs})")
            else:
                lines.append(f"        self.assertTrue({E.paren(E.seg(s.src, st.test))})")
        else:
            lines.extend(_indent(E.stmt_lines(s.src, st), 8))
    all_lines = E.lines_of(s.src)
    del all_lines[s.func.lineno - 1 : s.func.end_lineno]
    src = E.append_module("\n".join(all_lines), lines)
    return set_source(v, seed, src, ("import unittest",))


def assert_message(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None or t.node.msg is not None:
        return None
    parts = eq_parts(t)
    if parts is None:
        return None
    lhs, rhs, _l, _r = parts
    forms = {
        "plain": f'assert {lhs} == {rhs}, "unexpected result"',
        "repr_expected": f'assert {lhs} == {rhs}, "expected " + repr({rhs})',
        "parenthesised": f'assert ({lhs} == {rhs}), "regression"',
    }
    return set_source(v, seed, E.replace_stmt(t.src, t.node, [forms[sp]]))


def rebind_expected(v, seed, sp, rng):
    t = pick_assert(v, seed, rng)
    if t is None:
        return None
    parts = eq_parts(t)
    if parts is None or not E.is_literal(parts[3]):
        return None
    lhs, rhs, _l, _r = parts
    name = {"expected": "expected", "want": "want"}[sp]
    if name in E.names_used(t.func):
        return None
    src = E.replace_stmt(t.src, t.node, [f"{name} = {rhs}", f"assert {lhs} == {name}"])
    return set_source(v, seed, src)


def signature_cosmetics(v, seed, sp, rng):
    s = pick_test(v, seed, rng)
    if s is None:
        return None
    line = E.lines_of(s.src)[s.func.lineno - 1]
    if sp == "return_annotation":
        if not line.rstrip().endswith("):") or "->" in line:
            return None
        src = E.edit_def_line(s.src, s.func, lambda l: l.rstrip()[:-1] + " -> None:")
        return set_source(v, seed, src)
    if sp == "double_quotes_in_assert":
        tree = E.parse(s.src)
        if tree is None:
            return None
        lines = E.lines_of(s.src)
        eligible = [
            node for func, _cls in E.test_functions(tree) for node in E.direct_asserts(func)
            if node.lineno == node.end_lineno and "'" in lines[node.lineno - 1] and '"' not in lines[node.lineno - 1]
        ]
        if not eligible:
            return None
        node = rng.choice(eligible)
        lines[node.lineno - 1] = lines[node.lineno - 1].replace("'", '"')
        return set_source(v, seed, "\n".join(lines))
    if sp == "trailing_blank_lines":
        return set_source(v, seed, s.src.rstrip("\n") + "\n\n\n")
    return None


OPS = {
    "rename_local": ("naming", ("suffix_value", "actual", "result", "got"), rename_local),
    "docstring_comment": ("cosmetic", ("docstring", "comment_above_assert", "blank_line_above_assert"), docstring_comment),
    "extract_faithful": ("structure", ("positional", "keyword", "assert_equal"), extract_faithful),
    "split_test": ("structure", ("part2", "tail"), split_test),
    "merge_tests": ("structure", ("merge",), merge_tests),
    "approx_exact": ("assertion", ("approx_default", "approx_tight"), approx_exact),
    "parametrize_single": ("structure", ("arg_expected", "value_want"), parametrize_single),
    "to_unittest": ("dialect", ("assertEqual", "assertTrue"), to_unittest),
    "assert_message": ("assertion", ("plain", "repr_expected", "parenthesised"), assert_message),
    "rebind_expected": ("assertion", ("expected", "want"), rebind_expected),
    "signature_cosmetics": ("cosmetic", ("return_annotation", "double_quotes_in_assert", "trailing_blank_lines"), signature_cosmetics),
}
