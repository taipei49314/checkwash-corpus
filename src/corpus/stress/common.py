"""Shared shapes for the operator libraries."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from corpus.stress import edits as E
from corpus.stress.seeds import Seed


@dataclass
class Variant:
    """A seed's test side plus config files, after zero or more operators."""

    tests: dict[str, str]
    extras: dict[str, str]
    ops: list[tuple[str, str]] = field(default_factory=list)

    def copy(self) -> "Variant":
        return Variant(dict(self.tests), dict(self.extras), list(self.ops))

    @classmethod
    def from_seed(cls, seed: Seed) -> "Variant":
        return cls(dict(seed.tests), dict(seed.extras))


@dataclass
class Target:
    src: str
    tree: ast.Module
    func: ast.AST
    cls: ast.ClassDef | None
    node: ast.Assert
    block: list


@dataclass
class TestSite:
    src: str
    tree: ast.Module
    func: ast.AST
    cls: ast.ClassDef | None


def pick_assert(v: Variant, seed: Seed, rng) -> Target | None:
    src = v.tests[seed.main_test]
    tree = E.parse(src)
    if tree is None:
        return None
    sites = []
    for func, cls in E.test_functions(tree):
        for node in E.direct_asserts(func):
            sites.append((func, cls, node))
    if not sites:
        return None
    func, cls, node = rng.choice(sites)
    return Target(src, tree, func, cls, node, E.parent_block(func, node))


def pick_test(v: Variant, seed: Seed, rng) -> TestSite | None:
    src = v.tests[seed.main_test]
    tree = E.parse(src)
    if tree is None:
        return None
    funcs = E.test_functions(tree)
    if not funcs:
        return None
    func, cls = rng.choice(funcs)
    return TestSite(src, tree, func, cls)


def set_source(v: Variant, seed: Seed, src: str, imports: tuple[str, ...] = ()) -> Variant | None:
    for imp in imports:
        src = E.ensure_import(src, imp)
    if E.parse(src) is None:
        return None
    nv = v.copy()
    nv.tests[seed.main_test] = src
    return nv


def set_extra(v: Variant, path: str, text: str) -> Variant:
    nv = v.copy()
    nv.extras[path] = text
    return nv


def append_extra(v: Variant, path: str, text: str) -> Variant:
    nv = v.copy()
    existing = nv.extras.get(path, "")
    nv.extras[path] = (existing.rstrip("\n") + "\n\n" + text) if existing else text
    return nv


def eq_parts(t: Target):
    cmp = E.eq_compare(t.node)
    if cmp is None:
        return None
    lhs, rhs = cmp
    return E.paren(E.seg(t.src, lhs)), E.paren(E.seg(t.src, rhs)), lhs, rhs


def assert_body_lines(t: Target) -> list[str]:
    return E.stmt_lines(t.src, t.node)


def test_name(site) -> str:
    return site.func.name


def add_ini_option(ini: str, key: str, value: str) -> str:
    """Set or extend a `[pytest]` option; addopts values are appended."""
    lines = ini.rstrip("\n").split("\n") if ini.strip() else ["[pytest]"]
    if not any(line.strip().lower() == "[pytest]" for line in lines):
        lines.insert(0, "[pytest]")
    pat = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*)$")
    for i, line in enumerate(lines):
        m = pat.match(line)
        if m:
            if key == "addopts":
                lines[i] = f"{key} = {m.group(1).strip()} {value}".rstrip()
            else:
                lines[i] = f"{key} = {value}"
            return "\n".join(lines) + "\n"
    lines.append(f"{key} = {value}")
    return "\n".join(lines) + "\n"


def uses_self(site) -> bool:
    return site.cls is not None


def camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_") if part)
