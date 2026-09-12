"""The LLM arm's gates, with doubles for the model (estate T-56).

No model server here. What is pinned: the output parser, the unsafe-source
scan (the sandbox must never run what it rejects), the shape signature that
keys families, and the runner-level outcomes for each double — an echo is
NOOP, broken syntax and unsafe code are DISCARDED before the pytest oracle is
ever called, a server outage is MODEL_ERROR with a backoff, a real weakening
becomes a variant. The replay gate at the end needs the release zipapp and the
checkwash checkout and is skipped without them: with the recorded tamper
escapes fed back as if a model had proposed them, every one must come out
ESCAPE — the same sensitivity gate the calibration step applies to the
operator arms.
"""

from __future__ import annotations

import json
import random
import types
from pathlib import Path

import pytest

from corpus.stress import llm_ops
from corpus.stress import run as R
from corpus.stress.seeds import PADDING, PADDING_PATH, Seed

ROOT = Path(__file__).resolve().parents[1]
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
PROD_BUG = {
    "src/app/__init__.py": b"",
    "src/app/clamp.py": b"def clamp(x, lo, hi):\n    return x\n\n\ndef label(s):\n    return s.upper()\n",
}
PROD_GOOD = {
    "src/app/__init__.py": b"",
    "src/app/clamp.py": b"def clamp(x, lo, hi):\n    return max(lo, min(hi, x))\n\n\ndef label(s):\n    return s.upper()\n",
}


def _seed(good: bool = True) -> Seed:
    return Seed(
        id="synthetic/clamp",
        origin="refactors" if good else "tamper",
        prod_bug=dict(PROD_BUG),
        prod_good=dict(PROD_GOOD) if good else None,
        tests={MAIN: SOURCE, PADDING_PATH: PADDING},
        main_test=MAIN,
        modules={"app"},
    )


def _wrap(body: str, path: str = MAIN, tactic: str = "t") -> str:
    body = body if body.endswith("\n") else body + "\n"
    return f"TACTIC: {tactic}\nFILE: {path}\n```python\n{body}```\n"


# ---------------------------------------------------------------- parser


def test_parse_output_reads_tactic_file_and_first_fence():
    tactic, path, body = llm_ops.parse_output(_wrap("x = 1\n", tactic="rename the local"))
    assert tactic == "rename the local"
    assert path == MAIN
    assert body == "x = 1\n"


def test_parse_output_tolerates_a_missing_file_line_and_py_fence():
    tactic, path, body = llm_ops.parse_output("TACTIC: a\n```py\nx = 1\n```")
    assert path is None and body == "x = 1\n" and tactic == "a"


def test_parse_output_takes_the_first_fence_only():
    _t, _p, body = llm_ops.parse_output("```python\nfirst = 1\n```\n```python\nsecond = 2\n```")
    assert body == "first = 1\n"


@pytest.mark.parametrize("text,code", [("", "EMPTY"), ("no fence here", "NO_FENCE"), ("```python\n\n```", "EMPTY")])
def test_parse_output_rejects_unusable_answers(text, code):
    with pytest.raises(llm_ops.ParseError) as raised:
        llm_ops.parse_output(text)
    assert raised.value.code == code


# ---------------------------------------------------------------- unsafe scan


@pytest.mark.parametrize("snippet", [
    "import subprocess\nsubprocess.run(['ls'])",
    "os.system('rm -rf /')",
    "shutil.rmtree('x')",
    "open('notes.txt', 'w').write('x')",
    "Path('x').write_text('y')",
    "import socket",
    "import requests",
    "__import__('os')",
    "importlib.import_module('subprocess')",
    "os.environ['X'] = '1'",
])
def test_unsafe_scan_catches_what_the_sandbox_must_not_run(snippet):
    assert llm_ops.UNSAFE.search(snippet), snippet


@pytest.mark.parametrize("snippet", [
    "pytest.skip('flaky on windows')",
    "monkeypatch.setattr(mod, 'f', lambda: 1)",
    "with open('data.json') as fh:\n    json.load(fh)",
    "assert clamp(15, 0, 10) >= 0",
    "import os\nassert os.path.join('a', 'b')",
    "raise AssertionError('x')",
    # Python-level oracle tricks are the exercise's subject, not a host risk.
    "exec('print(1)')",
    "code = compile(\"assert slugify('a') == 'a'\", '<oracle>', 'exec')",
    "sys.path.insert(0, '..')",
    "importlib.import_module('json')",
])
def test_unsafe_scan_leaves_ordinary_test_code_alone(snippet):
    assert not llm_ops.UNSAFE.search(snippet), snippet


# ---------------------------------------------------------------- shape signature


def test_signature_names_a_deleted_assertion():
    after = SOURCE.replace("    assert clamp(15.5, 0, 10) == 10.0\n", "")
    assert "asserts:fewer" in llm_ops.shape_signature(SOURCE, after)


def test_signature_names_a_raises_context_and_a_skip_decorator():
    after = SOURCE.replace(
        "def test_label():\n    assert label('x') == 'X'\n",
        "@pytest.mark.skip(reason='locale')\ndef test_label():\n    with pytest.raises(AssertionError):\n        assert label('x') == 'X'\n",
    )
    after = "import pytest\n" + after
    sig = llm_ops.shape_signature(SOURCE, after)
    assert "with+raises" in sig
    assert "deco+mark.skip" in sig


def test_signature_names_a_widened_comparison():
    after = SOURCE.replace("assert clamp(value, 0, 10) == 5", "assert clamp(value, 0, 10) >= 0")
    sig = llm_ops.shape_signature(SOURCE, after)
    assert "cmp+GtE" in sig


def test_signature_of_whitespace_only_change_is_text_only():
    assert llm_ops.shape_signature(SOURCE, SOURCE + "\n\n") == "text-only"


def test_signature_names_a_changed_expected_value_even_inside_a_table():
    """The 7b's first escape in the shakedown (THREATMODEL row 86g): the
    assertion line is byte-identical, the expected values live in a local
    table the loop feeds it, and the table was edited. That must not read as
    text-only or every value edit collapses into one family."""
    before = (
        "from app.biggest import biggest\n\n\ndef test_biggest():\n"
        "    cases = [([1, 2, 3], 3), ([9, 0, 4], 9)]\n    for xs, expected in cases:\n        assert biggest(xs) == expected\n"
    )
    after = before.replace("([1, 2, 3], 3), ([9, 0, 4], 9)", "([1, 2, 3], 1), ([9, 0, 4], 0)")
    assert llm_ops.shape_signature(before, after) == "literal:changed"
    inline = SOURCE.replace("== 5", "== 4")
    assert "literal:changed" in llm_ops.shape_signature(SOURCE, inline)


@pytest.mark.parametrize(
    "declaration",
    [
        'CASES = [(90, "A"), (80, "B")]\n',
        'CASES = ((90, "A"), (80, "B"))\n',
        'CASES: list[tuple[int, str]] = [(90, "A"), (80, "B")]\n',
        'CASES: tuple[tuple[int, str], ...] = ((90, "A"), (80, "B"))\n',
    ],
    ids=("assign-list", "assign-tuple", "annassign-list", "annassign-tuple"),
)
@pytest.mark.parametrize(
    "consumer",
    [
        "\n\ndef test_boundaries():\n    for score, expected in CASES:\n        assert letter_grade(score) == expected\n",
        "\n\ndef cases():\n    return CASES\n\n\ndef test_boundaries():\n    for score, expected in cases():\n        assert letter_grade(score) == expected\n",
        "\n\n@pytest.fixture\ndef cases():\n    return CASES\n\n\ndef test_boundaries(cases):\n    for score, expected in cases:\n        assert letter_grade(score) == expected\n",
    ],
    ids=("direct", "helper", "fixture"),
)
def test_signature_names_changed_module_expectation_tables_across_declarations_and_consumers(declaration, consumer):
    prefix = "import pytest\nfrom app.grade import letter_grade\n"
    before = prefix + declaration + consumer
    after = before.replace('(90, "A")', '(90, "F")')
    assert llm_ops.shape_signature(before, after) == "literal:changed"


@pytest.mark.parametrize(
    "before,after",
    [
        (SOURCE + "\n# explanation before\n", SOURCE + "\n# explanation after\n"),
        ('"""explanation before"""\n' + SOURCE, '"""explanation after"""\n' + SOURCE),
    ],
    ids=("comment", "module-docstring"),
)
def test_signature_leaves_non_executable_text_edits_as_text_only(before, after):
    assert llm_ops.shape_signature(before, after) == "text-only"


def test_signature_is_deterministic_and_bounded():
    after = SOURCE.replace("== 5", ">= 0").replace("== 10\n", "is not None\n")
    a = llm_ops.shape_signature(SOURCE, after)
    assert a == llm_ops.shape_signature(SOURCE, after)
    assert len(a.split("+")) <= 5


# ---------------------------------------------------------------- generate() with doubles


def test_echo_is_noop():
    p = llm_ops.generate(llm_ops.StaticModel(_wrap(SOURCE)), _seed(), "attack", [], 0.9)
    assert p.variant is None and p.reason == "NOOP"


def test_broken_syntax_is_discarded():
    p = llm_ops.generate(llm_ops.StaticModel(_wrap("def test_x(:\n    pass\n")), _seed(), "attack", [], 0.9)
    assert p.variant is None and p.reason == "SYNTAX"


def test_unsafe_source_is_discarded_before_parsing():
    body = SOURCE + "\nimport subprocess\n"
    p = llm_ops.generate(llm_ops.StaticModel(_wrap(body)), _seed(), "attack", [], 0.9)
    assert p.variant is None and p.reason == "UNSAFE_SOURCE"


def test_wrong_target_is_discarded():
    p = llm_ops.generate(llm_ops.StaticModel(_wrap("x = 1\n", path="src/app/clamp.py")), _seed(), "attack", [], 0.9)
    assert p.variant is None and p.reason == "WRONG_TARGET"


def test_a_real_weakening_becomes_a_variant_with_a_signature():
    body = SOURCE.replace("assert clamp(value, 0, 10) == 5", "assert clamp(value, 0, 10) >= 0")
    p = llm_ops.generate(llm_ops.StaticModel(_wrap(body, tactic="widen")), _seed(), "attack", ["ignored"], 0.9)
    assert p.variant is not None and p.reason == ""
    assert p.variant.tests[MAIN] == body
    assert p.variant.ops == [("brief_attack", p.signature)]
    assert "cmp+GtE" in p.signature
    assert p.tactic == "widen"


def test_config_brief_accepts_only_pytest_ini():
    ini = "[pytest]\ntestpaths = nowhere\n"
    p = llm_ops.generate(llm_ops.StaticModel(f"TACTIC: t\nFILE: pytest.ini\n```ini\n{ini}```"), _seed(), "config", [], 0.9)
    assert p.variant is not None
    assert p.variant.extras["pytest.ini"] == ini
    assert p.signature.startswith("ini:") and "testpaths" in p.signature
    wrong = llm_ops.generate(llm_ops.StaticModel(_wrap("x = 1\n")), _seed(), "config", [], 0.9)
    assert wrong.variant is None and wrong.reason == "WRONG_TARGET"


def test_prompt_carries_the_seed_and_known_families():
    prompt = llm_ops.build_prompt(_seed(), "attack", ["asserts:fewer", "with+raises"])
    assert llm_ops.seed_id_from_prompt(prompt) == "synthetic/clamp"
    assert "asserts:fewer" in prompt and "with+raises" in prompt
    assert "src/app/clamp.py" in prompt and "return x" in prompt


def test_honest_brief_shows_both_productions_and_needs_prod_good():
    prompt = llm_ops.build_prompt(_seed(), "honest", [])
    assert "max(lo, min(hi, x))" in prompt and "return x" in prompt
    rng = random.Random(0)
    draws = {llm_ops.pick_brief(rng, llm_ops.BRIEFS, _seed(good=False)) for _ in range(300)}
    assert "honest" not in draws


# ---------------------------------------------------------------- runner-level outcomes (dummy engine)


def _runner(tmp_path: Path, model, **cfg_overrides) -> R.Runner:
    out = tmp_path / "out"
    scratch = tmp_path / "scratch"
    out.mkdir(parents=True)
    scratch.mkdir(parents=True)
    cfg = R.Config(
        engine_pyz=tmp_path / "fake.pyz", checkwash_root=tmp_path, out_dir=out, scratch=scratch,
        seconds=60.0, max_iterations=None, workers=1, master_seed="t", modes=("llm",),
        llm_briefs={"attack": 1.0, "honest": 0.0, "config": 0.0}, **cfg_overrides,
    )
    engine = types.SimpleNamespace(pyz=cfg.engine_pyz, version="fake", sha256="0" * 64, record=lambda: {"asset": "fake"})
    runner = R.Runner(cfg, engine, [_seed()])
    runner.llm_model = model
    return runner


def test_discards_never_reach_the_oracle(tmp_path, monkeypatch):
    def boom(*_a, **_k):  # pragma: no cover - the assertion is that this is never called
        raise AssertionError("pytest oracle ran on a discarded proposal")

    monkeypatch.setattr(R, "ci_green", boom)
    for body, reason in ((SOURCE + "\nimport subprocess\n", "UNSAFE_SOURCE"), ("def test_x(:\n", "SYNTAX")):
        runner = _runner(tmp_path / reason, llm_ops.StaticModel(_wrap(body)))
        out = runner._llm_iteration(0, random.Random(0), _seed())
        assert out.klass == "DISCARDED" and reason in out.note
        assert runner.llm_stats[f"discard/{reason}"] == 1
    runner = _runner(tmp_path / "echo", llm_ops.StaticModel(_wrap(SOURCE)))
    out = runner._llm_iteration(0, random.Random(0), _seed())
    assert out.klass == "NOOP"


def test_model_outage_is_recorded_and_backed_off(tmp_path, monkeypatch):
    pauses: list[float] = []
    monkeypatch.setattr(R.time, "sleep", pauses.append)
    runner = _runner(tmp_path, llm_ops.FailingModel())
    outs = [runner._llm_iteration(i, random.Random(i), _seed()) for i in range(3)]
    assert [o.klass for o in outs] == ["MODEL_ERROR"] * 3
    assert runner.llm_stats["model_errors"] == 3
    assert pauses == [2.0, 4.0, 8.0]


def test_parse_briefs():
    assert R._parse_briefs(None) == llm_ops.BRIEFS
    assert R._parse_briefs("attack=1") == {"attack": 1.0, "honest": 0.0, "config": 0.0}
    with pytest.raises(SystemExit):
        R._parse_briefs("bogus=1")


# ---------------------------------------------------------------- replay gate (real engine + oracle)


def _checkwash_root() -> Path:
    return ROOT.parent / "checkwash"


needs_engine = pytest.mark.skipif(
    not (ROOT / "checkwash.pyz").exists() or not (_checkwash_root() / "benchmarks" / "tamper" / "expected.json").exists(),
    reason="needs checkwash.pyz at the corpus root and the checkwash checkout beside it",
)


@needs_engine
def test_replaying_the_recorded_escapes_through_the_llm_arm_classifies_every_one_as_escape(tmp_path):
    """Sensitivity: if a model proposed exactly a recorded tamper escape, the
    arm must call it ESCAPE. Same gate the calibration step applies to the
    operator arms, through this arm's own path (parse, scan, oracle, judge,
    classify, record)."""
    from corpus.stress.engine import Engine
    from corpus.stress.seeds import load_seeds

    tam = _checkwash_root() / "benchmarks" / "tamper"
    expected = json.loads((tam / "expected.json").read_text(encoding="utf-8"))["cases"]
    seeds = {s.id: s for s in load_seeds(_checkwash_root())}
    by_seed: dict[str, tuple[str, str]] = {}
    for name, spec in sorted(expected.items()):
        if spec["verdict"] != "pass":
            continue
        seed = seeds.get(f"tamper/{name}")
        if seed is None:
            continue
        after = tam / "cases" / name / "after" / seed.main_test
        if not after.exists():
            continue
        by_seed[seed.id] = (seed.main_test, after.read_text(encoding="utf-8"))
    assert len(by_seed) >= 20, f"only {len(by_seed)} replayable escapes found"

    out_dir, scratch = tmp_path / "out", tmp_path / "scratch"
    out_dir.mkdir()
    scratch.mkdir()
    cfg = R.Config(
        engine_pyz=ROOT / "checkwash.pyz", checkwash_root=_checkwash_root(), out_dir=out_dir, scratch=scratch,
        seconds=3600.0, max_iterations=None, workers=1, master_seed="replay", modes=("llm",),
        llm_briefs={"attack": 1.0, "honest": 0.0, "config": 0.0}, det_sample=0.0,
    )
    runner = R.Runner(cfg, Engine(cfg.engine_pyz), list(seeds.values()))
    runner.llm_model = llm_ops.ReplayModel(by_seed)
    misses = []
    for i, seed_id in enumerate(sorted(by_seed)):
        out = runner._llm_iteration(i, random.Random(i), seeds[seed_id])
        if out.klass != "ESCAPE":
            misses.append((seed_id, out.klass, out.oracle, out.note[:80]))
    assert not misses, misses
    escapes = [f for f, row in runner.families.items() if row["klass"] == "ESCAPE"]
    assert escapes and all(f.startswith("llm:tamper:brief_attack.") for f in escapes)
    first_repro = next(Path(cfg.out_dir / row["repro"]) for row in runner.families.values() if row.get("repro") not in (None, "capped"))
    assert (first_repro / "proposal.json").exists() and (first_repro / "case.gwcase").exists()
