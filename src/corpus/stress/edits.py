"""Surgical source editing anchored on AST positions.

Mutants are line-level edits — never a whole-file `ast.unparse` — so the
before → after diff carries only the intended change. A harness that
reformats every line would make its own noise indistinguishable from the
engine's verdict.
"""

from __future__ import annotations

import ast
import re

TEST_PREFIX = "test"


def parse(src: str) -> ast.Module | None:
    try:
        return ast.parse(src)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None


def lines_of(src: str) -> list[str]:
    return src.split("\n")


def test_functions(tree: ast.Module) -> list[tuple[ast.AST, ast.ClassDef | None]]:
    out: list[tuple[ast.AST, ast.ClassDef | None]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith(TEST_PREFIX):
                out.append((node, None))
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name.startswith(TEST_PREFIX):
                        out.append((child, node))
    return out


def is_docstring(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(getattr(stmt, "value", None), ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def body_statements(func) -> list[ast.stmt]:
    """Top-level statements of a function body, docstring excluded."""
    body = list(func.body)
    if body and is_docstring(body[0]):
        body = body[1:]
    return body


def direct_asserts(func) -> list[ast.Assert]:
    """Assert statements the function runs itself: nested defs are skipped."""
    out: list[ast.Assert] = []
    stack: list[ast.stmt] = list(func.body)
    while stack:
        st = stack.pop(0)
        if isinstance(st, ast.Assert):
            out.append(st)
            continue
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for attr in ("body", "orelse", "finalbody"):
            block = getattr(st, attr, None)
            if isinstance(block, list):
                stack.extend(s for s in block if isinstance(s, ast.stmt))
        for handler in getattr(st, "handlers", None) or []:
            stack.extend(handler.body)
    return sorted(out, key=lambda n: (n.lineno, n.col_offset))


def parent_block(func, node: ast.stmt) -> list[ast.stmt]:
    """The statement list that directly contains `node` (defaults to func.body)."""
    stack: list[list[ast.stmt]] = [func.body]
    while stack:
        block = stack.pop()
        if any(s is node for s in block):
            return block
        for st in block:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for attr in ("body", "orelse", "finalbody"):
                sub = getattr(st, attr, None)
                if isinstance(sub, list) and sub and isinstance(sub[0], ast.stmt):
                    stack.append(sub)
            for handler in getattr(st, "handlers", None) or []:
                stack.append(handler.body)
    return func.body


def eq_compare(node: ast.Assert):
    test = node.test
    if (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
    ):
        return test.left, test.comparators[0]
    return None


def seg(src: str, node: ast.AST) -> str:
    return ast.get_source_segment(src, node) or ""


def paren(expr: str) -> str:
    return f"({expr})" if "\n" in expr else expr


def indent_at(src: str, lineno: int) -> str:
    line = lines_of(src)[lineno - 1]
    return line[: len(line) - len(line.lstrip(" \t"))]


def stmt_lines(src: str, node: ast.stmt) -> list[str]:
    """The statement's own lines with its base indentation stripped."""
    ind = indent_at(src, node.lineno)
    raw = lines_of(src)[node.lineno - 1 : node.end_lineno]
    out = []
    for line in raw:
        out.append(line[len(ind) :] if line.startswith(ind) else line.lstrip(" \t"))
    return out


def replace_stmt(src: str, node: ast.stmt, new_lines: list[str]) -> str:
    lines = lines_of(src)
    ind = indent_at(src, node.lineno)
    start, end = node.lineno - 1, node.end_lineno
    new = [(ind + line) if line.strip() else "" for line in new_lines]
    return "\n".join(lines[:start] + new + lines[end:])


def delete_stmt(src: str, node: ast.stmt, block: list[ast.stmt]) -> str:
    if len(block) == 1:
        return replace_stmt(src, node, ["pass"])
    lines = lines_of(src)
    return "\n".join(lines[: node.lineno - 1] + lines[node.end_lineno :])


def insert_before(src: str, lineno: int, new_lines: list[str], indent: str = "") -> str:
    lines = lines_of(src)
    new = [(indent + line) if line.strip() else "" for line in new_lines]
    return "\n".join(lines[: lineno - 1] + new + lines[lineno - 1 :])


def last_import_end(tree: ast.Module) -> int:
    end = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end = max(end, node.end_lineno or node.lineno)
    return end


def insert_after_imports(src: str, tree: ast.Module, new_lines: list[str]) -> str:
    end = last_import_end(tree)
    if end == 0 and tree.body and is_docstring(tree.body[0]):
        end = tree.body[0].end_lineno or 1
    return insert_before(src, end + 1, new_lines)


def has_import(tree: ast.Module, text: str) -> bool:
    want = text.strip()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if ast.unparse(node).strip() == want:
                return True
    return False


def ensure_import(src: str, text: str) -> str:
    tree = parse(src)
    if tree is None or has_import(tree, text):
        return src
    return insert_after_imports(src, tree, [text])


def append_module(src: str, new_lines: list[str]) -> str:
    return src.rstrip("\n") + "\n\n\n" + "\n".join(new_lines) + "\n"


def decorator_insert_line(func) -> int:
    if func.decorator_list:
        return min(d.lineno for d in func.decorator_list)
    return func.lineno


def insert_decorator(src: str, func, text: str) -> str:
    return insert_before(src, decorator_insert_line(func), [text], indent_at(src, func.lineno))


def body_insert_point(func) -> int:
    stmts = body_statements(func)
    target = stmts[0] if stmts else func.body[0]
    return target.lineno


def insert_first_statement(src: str, func, new_lines: list[str]) -> str:
    line = body_insert_point(func)
    return insert_before(src, line, new_lines, indent_at(src, line))


def edit_def_line(src: str, func, transform) -> str:
    lines = lines_of(src)
    idx = func.lineno - 1
    lines[idx] = transform(lines[idx])
    return "\n".join(lines)


def add_first_param(line: str, name: str) -> str:
    """`def f(` → `def f(name, ` keeping `self` first when present."""
    head, sep, tail = line.partition("(")
    if not sep:
        return line
    stripped = tail.lstrip()
    if stripped.startswith(")"):
        return f"{head}({name}{tail}"
    if stripped.startswith("self"):
        rest = stripped[len("self") :]
        rest = rest.lstrip()
        if rest.startswith(")"):
            return f"{head}(self, {name}{rest}"
        if rest.startswith(","):
            return f"{head}(self, {name},{rest[1:]}"
    return f"{head}({name}, {tail}"


def rename_in_range(src: str, start: int, end: int, old: str, new: str) -> str:
    lines = lines_of(src)
    pat = re.compile(rf"(?<![\w.]){re.escape(old)}(?!\w)")
    for i in range(start - 1, end):
        lines[i] = pat.sub(new, lines[i])
    return "\n".join(lines)


def replace_expr(src: str, node: ast.expr, text: str) -> str | None:
    """Replace a single-line expression node in place; None if it spans lines."""
    if node.lineno != node.end_lineno:
        return None
    lines = lines_of(src)
    line = lines[node.lineno - 1]
    lines[node.lineno - 1] = line[: node.col_offset] + text + line[node.end_col_offset :]
    return "\n".join(lines)


def is_literal(node: ast.AST) -> bool:
    try:
        ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return False
    return True


def is_number(node: ast.AST) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        node = node.operand
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def import_of(tree: ast.Module, name: str) -> tuple[str, int] | None:
    """(module, lineno) of the `from module import name` that binds `name`."""
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                if (alias.asname or alias.name) == name:
                    return node.module, node.lineno
    return None


def local_names(func) -> list[str]:
    out: list[str] = []
    for st in body_statements(func):
        if isinstance(st, ast.Assign):
            for target in st.targets:
                if isinstance(target, ast.Name) and target.id not in out:
                    out.append(target.id)
    return out


def names_used(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
