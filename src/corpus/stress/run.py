"""The loop: generate, verify with pytest, judge with the pinned engine, classify,
minimise, re-verify through the CLI, record. Plus the calibration gates that
have to pass before any 24-hour number is believed.
"""

from __future__ import annotations

import datetime
import json
import random
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

from corpus.stress import honest_ops, llm_ops, random_ops, tamper_ops
from corpus.stress import report as R
from corpus.stress.common import Variant
from corpus.stress.engine import Engine, Judgement, blackbox_check
from corpus.stress.sandbox import Workspace, ci_green, materialise
from corpus.stress.seeds import Seed, load_seeds

MODE_WEIGHTS = {"rules": 0.6, "open": 0.25, "robust": 0.15, "llm": 0.25}
REGISTRIES = {"tamper": tamper_ops.OPS, "honest": honest_ops.OPS, "open": random_ops.OPS}


@dataclass
class Config:
    engine_pyz: Path
    checkwash_root: Path
    out_dir: Path
    scratch: Path
    seconds: float
    max_iterations: int | None
    workers: int
    master_seed: str
    modes: tuple[str, ...]
    python: str | None = None
    perf_budget_s: float = 1.0
    perf_budget_mega_s: float = 2.5
    honest_share: float = 0.35
    checkpoint_every: int = 40
    det_sample: float = 0.05
    oracle_timeout: int = 60
    max_repros_per_class: int = 300
    # LLM arm (estate T-56): a local model proposes, this harness decides.
    llm_url: str = "http://127.0.0.1:11434"
    llm_model: str = "qwen2.5-coder:7b"
    llm_api: str = "auto"
    llm_temperature: float = 0.9
    llm_num_ctx: int = 8192
    llm_timeout: int = 600
    llm_briefs: dict = field(default_factory=lambda: dict(llm_ops.BRIEFS))


@dataclass
class Outcome:
    iteration: int
    mode: str
    kind: str
    seed_id: str
    ops: list[list[str]]
    oracle: str
    verdict: str | None
    rules: list[str]
    seconds: float
    deterministic: bool | None
    klass: str
    family: str
    blackbox: str | None = None
    divergence: bool = False
    note: str = ""
    minimized_from: list[list[str]] | None = None


# ---------------------------------------------------------------- diffs

def _bytes(value) -> bytes | None:
    if value is None:
        return None
    return value if isinstance(value, bytes) else value.encode("utf-8")


def build_changes(seed: Seed, tests_after: dict, extras_after: dict, head_prod: dict[str, bytes]):
    before: dict[str, bytes] = {}
    for path, text in seed.tests.items():
        before[path] = _bytes(text)
    for path, text in seed.extras.items():
        before[path] = _bytes(text)
    after: dict[str, bytes | None] = dict(before)
    for path, text in tests_after.items():
        after[path] = _bytes(text)
    for path, text in extras_after.items():
        after[path] = _bytes(text)
    changes = []
    for path in sorted(set(before) | set(after)):
        b, a = before.get(path), after.get(path)
        if b == a:
            continue
        changes.append((path, b, a))
    before_files = {**head_prod, **before}
    after_files: dict[str, bytes | None] = {**head_prod, **after}
    return changes, before_files, after_files


# ---------------------------------------------------------------- generation

def _pick_mode(rng: random.Random, modes: tuple[str, ...]) -> str:
    weights = [MODE_WEIGHTS[m] for m in modes]
    return rng.choices(list(modes), weights=weights, k=1)[0]


def _chain_length(rng: random.Random, mode: str) -> int:
    r = rng.random()
    if mode == "open":
        return 1 if r < 0.5 else (2 if r < 0.85 else 3)
    return 1 if r < 0.7 else (2 if r < 0.95 else 3)


def draw_chain(rng: random.Random, registry: dict, length: int) -> list[tuple[str, str]]:
    chain = []
    names = sorted(registry)
    for _ in range(length):
        name = rng.choice(names)
        _family, spellings, _fn = registry[name]
        chain.append((name, rng.choice(list(spellings))))
    return chain


def apply_chain(seed: Seed, registry: dict, chain: list[tuple[str, str]], master: str, iteration: int) -> Variant | None:
    v = Variant.from_seed(seed)
    for idx, (name, spelling) in enumerate(chain):
        sub = random.Random(f"{master}:{iteration}:{idx}:{name}:{spelling}")
        fn = registry[name][2]
        nv = fn(v, seed, spelling, sub)
        if nv is None:
            return None
        nv.ops = v.ops + [(name, spelling)]
        v = nv
    return v


# ---------------------------------------------------------------- the runner

class Runner:
    def __init__(self, cfg: Config, engine: Engine, seeds: list[Seed]):
        self.cfg = cfg
        self.engine = engine
        self.seeds = seeds
        self.lock = threading.Lock()
        self.engine_lock = threading.Lock()
        # Counters only: a day is ~10^6 iterations, and keeping every Outcome
        # in memory would cost more than the engine under test.
        self.by_mode: dict[str, Counter] = {}
        self.engine_seconds_total = 0.0
        self.families: dict[str, dict] = {}
        self.repro_counts: Counter = Counter()
        self.coverage: dict[str, dict] = {}
        self.perf_suspects: list[dict] = []
        self.started = time.time()
        self.iterations_done = 0
        self.stream = (cfg.scratch / f"{cfg.out_dir.name}-outcomes.jsonl").open("a", encoding="utf-8")
        self.stop = threading.Event()
        # LLM arm: the model is created lazily (tests inject doubles); stats by
        # brief and discard reason; a backoff so a dead server does not turn
        # the loop into a tight retry.
        self.llm_model = None
        self.llm_stats: Counter = Counter()
        self.llm_consecutive_errors = 0

    # -- oracle -------------------------------------------------------------
    def _green(self, prod: dict[str, bytes], tests: dict, extras: dict, label: str) -> str:
        with Workspace(self.cfg.scratch, label) as ws:
            materialise(ws, prod, tests, extras)
            return ci_green(ws, self.cfg.python, self.cfg.oracle_timeout)

    def verify(self, seed: Seed, kind: str, tests: dict, extras: dict) -> str:
        """'verified' | 'discarded' | 'timeout' | 'error' — the mechanical oracle."""
        bug = self._green(seed.prod_bug, tests, extras, "bug")
        if bug in ("timeout", "error"):
            return bug
        if kind in ("tamper", "open"):
            return "verified" if bug == "green" else "discarded"
        if bug == "green":
            return "discarded"  # no longer catches the bug
        good = self._green(seed.prod_good or {}, tests, extras, "good")
        if good in ("timeout", "error"):
            return good
        return "verified" if good == "green" else "discarded"

    # -- judging -----------------------------------------------------------
    def judge(self, changes, head, modules, *, twice: bool) -> tuple[Judgement, bool | None]:
        with self.engine_lock:
            if twice:
                return self.engine.judge_twice(changes, head, modules)
            return self.engine.judge(changes, head, modules), None

    # -- coverage ----------------------------------------------------------
    def _cover(self, key: str, field_name: str) -> None:
        row = self.coverage.setdefault(key, {"generated": 0, "applicable": 0, "verified": 0, "findings": 0})
        row[field_name] += 1

    # -- one iteration -----------------------------------------------------
    def iteration(self, i: int) -> Outcome:
        cfg = self.cfg
        rng = random.Random(f"{cfg.master_seed}:{i}")
        mode = _pick_mode(rng, cfg.modes)
        seed = rng.choice(self.seeds)
        if mode == "robust":
            return self._robust_iteration(i, rng, seed)
        if mode == "llm":
            return self._llm_iteration(i, rng, seed)
        kind = "open" if mode == "open" else (
            "honest" if seed.honest_capable and rng.random() < cfg.honest_share else "tamper"
        )
        registry = REGISTRIES[kind]
        chain = draw_chain(rng, registry, _chain_length(rng, mode))
        for name, sp in chain:
            self._cover(f"{mode}/{kind}/{name}/{sp}", "generated")
        variant = apply_chain(seed, registry, chain, cfg.master_seed, i)
        ops = [list(c) for c in chain]
        if variant is None:
            return Outcome(i, mode, kind, seed.id, ops, "n/a", None, [], 0.0, None, "INAPPLICABLE", "")
        for name, sp in chain:
            self._cover(f"{mode}/{kind}/{name}/{sp}", "applicable")
        head = seed.prod_good if kind == "honest" else seed.prod_bug
        changes, before_files, after_files = build_changes(seed, variant.tests, variant.extras, head)
        if not changes:
            return Outcome(i, mode, kind, seed.id, ops, "n/a", None, [], 0.0, None, "NOOP", "")
        oracle = self.verify(seed, kind, variant.tests, variant.extras)
        if oracle != "verified":
            klass = {"discarded": "DISCARDED", "timeout": "ORACLE_TIMEOUT", "error": "ORACLE_ERROR"}[oracle]
            return Outcome(i, mode, kind, seed.id, ops, oracle, None, [], 0.0, None, klass, "")
        for name, sp in chain:
            self._cover(f"{mode}/{kind}/{name}/{sp}", "verified")
        twice = rng.random() < cfg.det_sample
        judgement, det = self.judge(changes, head, seed.modules, twice=twice)
        return self._classify(i, mode, kind, seed, chain, variant, changes, before_files, after_files, head, judgement, det)

    def _classify(self, i, mode, kind, seed, chain, variant, changes, before_files, after_files, head, judgement, det):
        cfg = self.cfg
        ops = [list(c) for c in chain]
        if judgement.verdict == "error":
            fam = "crash:" + (judgement.error or "").strip().split("\n")[0][:120]
            out = Outcome(i, mode, kind, seed.id, ops, "verified", "error", [], judgement.seconds, det, "CRASH", fam, note=judgement.error or "")
            self._record_family(out, seed, variant, changes, before_files, after_files, head, judgement)
            return out
        klass = "OK"
        if kind in ("tamper", "open") and judgement.verdict != "block":
            klass = "ESCAPE"
        elif kind == "honest" and judgement.verdict == "block":
            klass = "FALSE_POSITIVE"
        if det is None and klass in ("ESCAPE", "FALSE_POSITIVE"):
            judgement, det = self.judge(changes, head, seed.modules, twice=True)
        family = ""
        minimized_from = None
        if klass in ("ESCAPE", "FALSE_POSITIVE"):
            reduced = None if mode == "llm" else self._minimize(seed, kind, chain, i, klass)
            if reduced is not None and reduced[0] != chain:
                minimized_from = ops
                chain, variant, changes, before_files, after_files, judgement = reduced
                ops = [list(c) for c in chain]
            family = f"{mode}:{kind}:" + "+".join(f"{n}.{s}" for n, s in chain)
            if klass == "FALSE_POSITIVE":
                family += ":" + ",".join(judgement.rules)
            if mode != "llm":
                for name, sp in chain:
                    self._cover(f"{mode}/{kind}/{name}/{sp}", "findings")
        if det is False:
            klass = "NONDET" if klass == "OK" else klass
            family = family or f"nondet:{mode}:" + "+".join(f"{n}.{s}" for n, s in chain)
        out = Outcome(i, mode, kind, seed.id, ops, "verified", judgement.verdict, judgement.rules, judgement.seconds, det, klass, family, minimized_from=minimized_from)
        if judgement.seconds > cfg.perf_budget_s:
            with self.lock:
                self.perf_suspects.append({"iteration": i, "seconds": judgement.seconds, "changes": changes, "head": head, "modules": sorted(seed.modules), "label": f"{mode}:{kind}:" + "+".join(f"{n}.{s}" for n, s in chain)})
        if klass in ("ESCAPE", "FALSE_POSITIVE", "NONDET") or det is False:
            self._record_family(out, seed, variant, changes, before_files, after_files, head, judgement)
        return out

    def _minimize(self, seed, kind, chain, i, klass):
        """Smallest sub-chain that still reproduces the class (singles, then pairs)."""
        if len(chain) < 2:
            return None
        registry = REGISTRIES[kind]
        head = seed.prod_good if kind == "honest" else seed.prod_bug
        candidates = [[c] for c in chain]
        if len(chain) == 3:
            candidates += [[chain[a], chain[b]] for a in range(3) for b in range(a + 1, 3)]
        for sub in candidates:
            variant = apply_chain(seed, registry, sub, self.cfg.master_seed, i)
            if variant is None:
                continue
            changes, before_files, after_files = build_changes(seed, variant.tests, variant.extras, head)
            if not changes or self.verify(seed, kind, variant.tests, variant.extras) != "verified":
                continue
            judgement, _det = self.judge(changes, head, seed.modules, twice=False)
            hit = (klass == "ESCAPE" and judgement.verdict not in ("block", "error")) or (
                klass == "FALSE_POSITIVE" and judgement.verdict == "block"
            )
            if hit:
                return sub, variant, changes, before_files, after_files, judgement
        return None

    def _record_family(self, out: Outcome, seed, variant, changes, before_files, after_files, head, judgement):
        with self.lock:
            row = self.families.get(out.family)
            first = row is None
            if first:
                row = {"klass": out.klass, "count": 0, "examples": [], "blackbox": None, "divergence": False, "repro": None}
                self.families[out.family] = row
            row["count"] += 1
            if len(row["examples"]) < 5:
                row["examples"].append(out.iteration)
        if not first:
            return
        blackbox, note = None, ""
        if out.klass in ("ESCAPE", "FALSE_POSITIVE"):
            with Workspace(self.cfg.scratch, "bb") as ws:
                blackbox, note = blackbox_check(self.engine.pyz, ws, before_files, after_files, self.cfg.python)
            out.blackbox = blackbox
            out.divergence = blackbox is not None and blackbox != judgement.verdict
        with self.lock:
            capped = self.repro_counts[out.klass] >= self.cfg.max_repros_per_class
            if not capped:
                self.repro_counts[out.klass] += 1
        repro = None if capped else R.write_repro(self.cfg.out_dir, out, seed, changes, head, judgement, before_files, after_files, self.engine.record())
        with self.lock:
            row["blackbox"] = blackbox
            row["blackbox_note"] = note
            row["divergence"] = out.divergence
            row["repro"] = "capped" if capped else (str(repro.relative_to(self.cfg.out_dir)).replace("\\", "/") if repro else None)

    # -- the LLM arm ----------------------------------------------------------
    def _llm(self):
        if self.llm_model is None:
            self.llm_model = llm_ops.make_model(
                self.cfg.llm_url, self.cfg.llm_model, self.cfg.llm_api,
                num_ctx=self.cfg.llm_num_ctx, timeout=self.cfg.llm_timeout,
            )
        return self.llm_model

    def _known_llm_families(self) -> list[str]:
        with self.lock:
            rows = [(fam, row["count"]) for fam, row in self.families.items() if fam.startswith("llm:")]
        rows.sort(key=lambda r: -r[1])
        return [fam.split(":", 2)[-1] for fam, _ in rows[:30]]

    def _llm_iteration(self, i, rng, seed):
        """Same gates as every other arm; only the proposal comes from a model.

        MODEL_ERROR is the server failing, backed off exponentially (2 s .. 60 s)
        and never counted as a finding. DISCARDED covers everything the parse
        gate, the unsafe-source scan and the oracle refuse — before pytest ever
        runs in the first two cases."""
        cfg = self.cfg
        brief = llm_ops.pick_brief(rng, cfg.llm_briefs, seed)
        kind = llm_ops.KIND_OF_BRIEF[brief]
        with self.lock:
            self.llm_stats[f"brief/{brief}/generated"] += 1
        try:
            proposal = llm_ops.generate(self._llm(), seed, brief, self._known_llm_families(), cfg.llm_temperature)
        except llm_ops.ModelError as exc:
            with self.lock:
                self.llm_consecutive_errors += 1
                self.llm_stats["model_errors"] += 1
                pause = min(60.0, 2.0 ** min(self.llm_consecutive_errors, 6))
            time.sleep(pause)
            return Outcome(i, "llm", kind, seed.id, [[f"brief_{brief}", "-"]], "n/a", None, [], 0.0, None, "MODEL_ERROR", "", note=str(exc)[:300])
        with self.lock:
            self.llm_consecutive_errors = 0
        if proposal.variant is None:
            with self.lock:
                self.llm_stats[f"discard/{proposal.reason}"] += 1
            klass = "NOOP" if proposal.reason == "NOOP" else "DISCARDED"
            return Outcome(i, "llm", kind, seed.id, [[f"brief_{brief}", "-"]], "n/a", None, [], 0.0, None, klass, "", note=f"{proposal.reason}; tactic={proposal.tactic}")
        variant = proposal.variant
        chain = [(f"brief_{brief}", proposal.signature)]
        ops = [list(c) for c in chain]
        head = seed.prod_good if kind == "honest" else seed.prod_bug
        changes, before_files, after_files = build_changes(seed, variant.tests, variant.extras, head)
        if not changes:
            with self.lock:
                self.llm_stats["discard/NOOP"] += 1
            return Outcome(i, "llm", kind, seed.id, ops, "n/a", None, [], 0.0, None, "NOOP", "", note=f"tactic={proposal.tactic}")
        oracle = self.verify(seed, kind, variant.tests, variant.extras)
        if oracle != "verified":
            klass = {"discarded": "DISCARDED", "timeout": "ORACLE_TIMEOUT", "error": "ORACLE_ERROR"}[oracle]
            with self.lock:
                self.llm_stats[f"discard/oracle_{oracle}"] += 1
            return Outcome(i, "llm", kind, seed.id, ops, oracle, None, [], 0.0, None, klass, "", note=f"tactic={proposal.tactic}")
        with self.lock:
            self.llm_stats[f"brief/{brief}/verified"] += 1
        twice = rng.random() < cfg.det_sample
        judgement, det = self.judge(changes, head, seed.modules, twice=twice)
        out = self._classify(i, "llm", kind, seed, chain, variant, changes, before_files, after_files, head, judgement, det)
        out.note = f"brief={brief}; model={self._llm().name}; tactic={proposal.tactic}"
        if out.klass in ("ESCAPE", "FALSE_POSITIVE"):
            with self.lock:
                self.llm_stats[f"brief/{brief}/{out.klass}"] += 1
                row = self.families.get(out.family) or {}
                first = row.get("examples") == [i]
                repro = row.get("repro")
            if first and repro and repro != "capped":
                R.write_proposal(cfg.out_dir / repro, proposal, self._llm().name)
        return out

    def _robust_iteration(self, i, rng, seed):
        sp = rng.choice(random_ops.ROBUST_SPELLINGS)
        self._cover(f"robust/robust/robust_inputs/{sp}", "generated")
        tests, extras = random_ops.robust_inputs(seed, sp, rng)
        head = seed.prod_bug
        changes, before_files, after_files = build_changes(seed, tests, extras, head)
        ops = [["robust_inputs", sp]]
        if not changes:
            judgement, det = self.judge([], head, seed.modules, twice=True)
            klass = "OK" if judgement.verdict != "error" and not judgement.findings else "CRASH"
            if judgement.verdict == "error":
                klass = "CRASH"
            elif judgement.findings:
                klass = "NOOP_FINDINGS"
            fam = f"robust:{sp}" if klass != "OK" else ""
            out = Outcome(i, "robust", "robust", seed.id, ops, "n/a", judgement.verdict, judgement.rules, judgement.seconds, det, klass, fam, note=judgement.error or "")
            if klass != "OK":
                self._record_family(out, seed, None, changes, before_files, after_files, head, judgement)
            return out
        self._cover(f"robust/robust/robust_inputs/{sp}", "applicable")
        judgement, det = self.judge(changes, head, seed.modules, twice=True)
        budget = self.cfg.perf_budget_mega_s if sp == "mega_diff_300" else self.cfg.perf_budget_s
        if judgement.verdict == "error":
            klass, fam = "CRASH", "crash:" + (judgement.error or "").strip().split("\n")[0][:120]
        elif judgement.verdict not in ("pass", "block"):
            klass, fam = "BAD_VERDICT", f"robust:{sp}:{judgement.verdict}"
        elif det is False:
            klass, fam = "NONDET", f"nondet:robust:{sp}"
        else:
            klass, fam = "OK", ""
        out = Outcome(i, "robust", "robust", seed.id, ops, "n/a", judgement.verdict, judgement.rules, judgement.seconds, det, klass, fam, note=(judgement.error or ""))
        if judgement.seconds > budget:
            with self.lock:
                self.perf_suspects.append({"iteration": i, "seconds": judgement.seconds, "changes": changes, "head": head, "modules": sorted(seed.modules), "label": f"robust:{sp}"})
        if klass != "OK":
            self._record_family(out, seed, None, changes, before_files, after_files, head, judgement)
        return out

    # -- bookkeeping -------------------------------------------------------
    def _log(self, out: Outcome) -> None:
        with self.lock:
            self.by_mode.setdefault(out.mode, Counter())[out.klass] += 1
            self.engine_seconds_total += out.seconds
            self.iterations_done += 1
            self.stream.write(json.dumps(asdict(out), ensure_ascii=False) + "\n")
            if self.iterations_done % self.cfg.checkpoint_every == 0:
                self.stream.flush()
                self.checkpoint(final=False)

    def checkpoint(self, *, final: bool) -> None:
        summary = R.summarise(self, final=final)
        R.write_summary(self.cfg.out_dir, summary)
        R.write_report(self.cfg.out_dir, summary, self)

    def remeasure_perf(self) -> list[dict]:
        """Re-time flagged inputs alone, after the workers drain: a budget miss
        measured under load is not a budget miss."""
        confirmed = []
        for row in self.perf_suspects:
            times = []
            for _ in range(3):
                j = self.engine.judge(row["changes"], row["head"], set(row["modules"]))
                times.append(j.seconds)
            median = sorted(times)[1]
            budget = self.cfg.perf_budget_mega_s if row["label"].endswith("mega_diff_300") else self.cfg.perf_budget_s
            if median > budget:
                confirmed.append({"iteration": row["iteration"], "label": row["label"], "under_load_s": round(row["seconds"], 3), "alone_median_s": round(median, 3), "budget_s": budget})
        return confirmed

    def run(self) -> None:
        deadline = self.started + self.cfg.seconds
        i = 0
        with ThreadPoolExecutor(max_workers=self.cfg.workers) as pool:
            pending = set()
            try:
                while True:
                    if (self.cfg.out_dir / "STOP").exists():
                        print("STOP file found — draining and writing the report", flush=True)
                        break
                    if time.time() >= deadline or (self.cfg.max_iterations is not None and i >= self.cfg.max_iterations):
                        break
                    while len(pending) < self.cfg.workers * 2 and (self.cfg.max_iterations is None or i < self.cfg.max_iterations) and time.time() < deadline:
                        pending.add(pool.submit(self._safe_iteration, i))
                        i += 1
                    done = next(as_completed(pending))
                    pending.discard(done)
                    result = done.result()
                    if result is not None:
                        self._log(result)
                for fut in as_completed(pending):
                    result = fut.result()
                    if result is not None:
                        self._log(result)
            except KeyboardInterrupt:
                self.stop.set()
                pool.shutdown(wait=False, cancel_futures=True)
                raise
        self.stream.flush()

    def _safe_iteration(self, i: int) -> Outcome | None:
        if self.stop.is_set():
            return None
        try:
            return self.iteration(i)
        except Exception as exc:  # noqa: BLE001 - harness bugs are logged, not fatal
            return Outcome(i, "harness", "harness", "", [], "n/a", None, [], 0.0, None, "HARNESS_ERROR", "harness:" + type(exc).__name__, note=f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------- seeds + calibration

def verify_seeds(seeds: list[Seed], cfg: Config) -> tuple[list[Seed], list[dict]]:
    """Every seed must be red on buggy production (and green on correct
    production when it ships one). Seeds that fail are dropped and listed."""
    kept, dropped = [], []
    for seed in seeds:
        with Workspace(cfg.scratch, "seed") as ws:
            materialise(ws, seed.prod_bug, seed.tests, seed.extras)
            bug = ci_green(ws, cfg.python, cfg.oracle_timeout)
        checks = {"bug_red": bug == "red"}
        if seed.prod_good is not None:
            with Workspace(cfg.scratch, "seed") as ws:
                materialise(ws, seed.prod_good, seed.tests, seed.extras)
                checks["good_green"] = ci_green(ws, cfg.python, cfg.oracle_timeout) == "green"
        seed.checks = checks
        (kept if all(checks.values()) else dropped).append(seed if all(checks.values()) else {"id": seed.id, "checks": checks})
    return kept, dropped


def _corpus_changes(before_root: Path, after_root: Path):
    paths = sorted(
        {str(p.relative_to(before_root)).replace("\\", "/") for p in before_root.rglob("*.py")}
        | {str(p.relative_to(after_root)).replace("\\", "/") for p in after_root.rglob("*.py")}
    )
    changes = []
    for path in paths:
        b, a = before_root / path, after_root / path
        changes.append((path, b.read_bytes() if b.exists() else None, a.read_bytes() if a.exists() else None))
    return changes


def _head(src: Path) -> dict[str, bytes]:
    return {f"src/{str(p.relative_to(src)).replace(chr(92), '/')}": p.read_bytes() for p in src.rglob("*.py")}


def calibrate(cfg: Config, engine: Engine) -> dict:
    """Three gates against recorded truth. Any failure means the plumbing is
    wrong and no generated number should be trusted."""
    root = cfg.checkwash_root
    result: dict = {"engine": engine.record(), "gates": {}}

    # Gate A: refactor corpus replays to exactly the recorded block set.
    ref = root / "benchmarks" / "refactors"
    expected = json.loads((ref / "expected.json").read_text(encoding="utf-8"))["cases"]
    mism, blocks = [], 0
    for name, spec in sorted(expected.items()):
        case = ref / "cases" / name
        changes = _corpus_changes(case / "BEFORE", case / "AFTER")
        j = engine.judge(changes, _head(case / "PROD-GOOD" / "src"), {"app"})
        is_block = j.verdict == "block"
        blocks += int(is_block)
        if is_block != bool(spec["blocks"]):
            mism.append({"case": name, "expected_block": spec["blocks"], "got": j.verdict, "rules": j.rules})
    result["gates"]["refactor_ledger"] = {"blocks": blocks, "expected_blocks": sum(1 for s in expected.values() if s["blocks"]), "mismatches": mism, "pass": not mism}

    # Gate B: tamper corpus replays to the recorded verdicts, and the harness's
    # own oracle agrees every case is BEFORE red / AFTER green.
    tam = root / "benchmarks" / "tamper"
    expected_t = json.loads((tam / "expected.json").read_text(encoding="utf-8"))["cases"]
    mism_t, oracle_bad, blocks_t, escapes_seen = [], [], 0, 0
    for name, spec in sorted(expected_t.items()):
        case = tam / "cases" / name
        changes = _corpus_changes(case / "before", case / "after")
        j = engine.judge(changes, _head(case / "src"), {"app"})
        want = spec["verdict"]
        got = "block" if j.verdict == "block" else "pass"
        blocks_t += int(got == "block")
        if got != want:
            mism_t.append({"case": name, "expected": want, "got": j.verdict, "rules": j.rules})
        prod = _head(case / "src")
        tests_before = {str(p.relative_to(case / "before")).replace("\\", "/"): p.read_text(encoding="utf-8") for p in (case / "before").rglob("*.py")}
        tests_after = {str(p.relative_to(case / "after")).replace("\\", "/"): p.read_text(encoding="utf-8") for p in (case / "after").rglob("*.py")}
        with Workspace(cfg.scratch, "cal") as ws:
            materialise(ws, prod, tests_before, {})
            red = ci_green(ws, cfg.python, cfg.oracle_timeout)
        with Workspace(cfg.scratch, "cal") as ws:
            materialise(ws, prod, tests_after, {})
            green = ci_green(ws, cfg.python, cfg.oracle_timeout)
        if not (red == "red" and green == "green"):
            oracle_bad.append({"case": name, "before": red, "after": green})
        elif want == "pass" and got == "pass":
            escapes_seen += 1
    recorded_escapes = sum(1 for s in expected_t.values() if s["verdict"] == "pass")
    result["gates"]["tamper_ledger"] = {"blocks": blocks_t, "expected_blocks": sum(1 for s in expected_t.values() if s["verdict"] == "block"), "mismatches": mism_t, "pass": not mism_t}
    result["gates"]["oracle_plumbing"] = {"cases": len(expected_t), "oracle_disagreements": oracle_bad, "pass": not oracle_bad}
    result["gates"]["sensitivity"] = {"recorded_escapes": recorded_escapes, "classified_as_escape": escapes_seen, "pass": escapes_seen == recorded_escapes and not oracle_bad}
    result["pass"] = all(g["pass"] for g in result["gates"].values())
    return result


def _parse_briefs(spec: str | None) -> dict[str, float]:
    """`attack=0.6,honest=0.25,config=0.15`; unnamed briefs get weight 0."""
    weights = dict(llm_ops.BRIEFS)
    if not spec:
        return weights
    out: dict[str, float] = {}
    for part in spec.split(","):
        if not part.strip():
            continue
        name, _, value = part.partition("=")
        name = name.strip()
        if name not in weights:
            raise SystemExit(f"unknown brief {name!r}; want attack, honest, config")
        out[name] = float(value or 0)
    return {k: out.get(k, 0.0) for k in weights}


def make_config(args, root: Path) -> Config:
    engine = Path(args.engine).resolve()
    checkwash_root = Path(args.checkwash).resolve() if args.checkwash else (root.parent / "checkwash")
    day = datetime.date.today().isoformat()
    out = Path(args.out).resolve() if args.out else root / "records" / "stress" / day
    scratch = root / "clones" / ".stress-tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    if args.hours is not None and float(args.hours) <= 0:
        seconds = float("inf")  # --hours 0: run until a STOP file appears in the output dir, or Ctrl-C
    else:
        seconds = float(args.hours) * 3600.0 if args.hours else (float(args.minutes) * 60.0 if args.minutes else 24 * 3600.0)
    modes = tuple(m.strip() for m in (args.modes or "rules,open,robust").split(",") if m.strip())
    for m in modes:
        if m not in MODE_WEIGHTS:
            raise SystemExit(f"unknown mode {m!r}; want rules,open,robust,llm")
    return Config(
        engine_pyz=engine,
        checkwash_root=checkwash_root,
        out_dir=out,
        scratch=scratch,
        seconds=seconds,
        max_iterations=args.iterations,
        workers=max(1, int(args.workers)),
        master_seed=args.seed or day,
        modes=modes,
        python=args.python,
        llm_url=getattr(args, "llm_url", None) or "http://127.0.0.1:11434",
        llm_model=getattr(args, "llm_model", None) or "qwen2.5-coder:7b",
        llm_api=getattr(args, "llm_api", None) or "auto",
        llm_temperature=float(getattr(args, "llm_temperature", None) or 0.9),
        llm_num_ctx=int(getattr(args, "llm_num_ctx", None) or 8192),
        llm_timeout=int(getattr(args, "llm_timeout", None) or 600),
        llm_briefs=_parse_briefs(getattr(args, "llm_briefs", None)),
    )


def checkout_version(checkwash_root: Path) -> str | None:
    """The version the checkwash checkout beside us declares, or None."""
    try:
        import tomllib
        data = tomllib.loads((checkwash_root / "pyproject.toml").read_text(encoding="utf-8"))
        return str(data["project"]["version"])
    except Exception:  # noqa: BLE001 - no checkout, no opinion
        return None


def _vtuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split(".") if p.isdigit())


def stale_engine_message(engine_version: str, checkwash_root: Path) -> str | None:
    """Refuse to spend a day on an engine older than the checkout it is being
    measured against. The 2026-09-03 LLM-arm run judged 12,929 mutants with the
    v0.2.8 zipapp that happened to sit at the repository root while the
    checkout was at v0.2.12; 85 of its 88 escape families were later re-judged
    still open, but the run itself could not say so. Findings against a stale
    engine are not wrong, they are just about a version nobody ships."""
    current = checkout_version(checkwash_root)
    if current is None or not _vtuple(engine_version) or not _vtuple(current):
        return None
    if _vtuple(engine_version) < _vtuple(current):
        return (
            f"engine {engine_version} is older than the checkwash checkout ({current}) at {checkwash_root}. "
            "Download the current Release checkwash.pyz, or pass --allow-stale-engine to measure an old version on purpose."
        )
    return None


def cmd_calibrate(args, root: Path) -> int:
    cfg = make_config(args, root)
    engine = Engine(cfg.engine_pyz)
    stale = stale_engine_message(engine.version, cfg.checkwash_root)
    if stale and not getattr(args, "allow_stale_engine", False):
        print("refusing: " + stale, flush=True)
        return 2
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    seeds = load_seeds(cfg.checkwash_root)
    kept, dropped = verify_seeds(seeds, cfg)
    result = calibrate(cfg, engine)
    result["seeds"] = {"loaded": len(seeds), "usable": len(kept), "dropped": dropped}
    (cfg.out_dir / "calibration.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for name, gate in result["gates"].items():
        print(f"{'ok  ' if gate['pass'] else 'FAIL'} {name}: " + ", ".join(f"{k}={v}" for k, v in gate.items() if k not in ("pass", "mismatches", "oracle_disagreements")))
        for key in ("mismatches", "oracle_disagreements"):
            for row in gate.get(key, [])[:20]:
                print(f"       {row}")
    print(f"seeds: {len(kept)}/{len(seeds)} usable" + (f"; dropped {[d['id'] for d in dropped]}" if dropped else ""))
    print("calibration: " + ("PASS" if result["pass"] else "FAIL"))
    return 0 if result["pass"] else 1


def cmd_run(args, root: Path) -> int:
    cfg = make_config(args, root)
    engine = Engine(cfg.engine_pyz)
    stale = stale_engine_message(engine.version, cfg.checkwash_root)
    if stale and not getattr(args, "allow_stale_engine", False):
        print("refusing: " + stale, flush=True)
        return 2
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    seeds = load_seeds(cfg.checkwash_root)
    kept, dropped = verify_seeds(seeds, cfg)
    if not kept:
        print("no usable seeds", flush=True)
        return 2
    calibration_path = cfg.out_dir / "calibration.json"
    if not calibration_path.exists() and not args.skip_calibration:
        print("calibrating against recorded truth first ...", flush=True)
        result = calibrate(cfg, engine)
        result["seeds"] = {"loaded": len(seeds), "usable": len(kept), "dropped": dropped}
        calibration_path.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        if not result["pass"]:
            print("calibration FAILED — refusing to run; see calibration.json", flush=True)
            return 1
        print("calibration PASS", flush=True)
    runner = Runner(cfg, engine, kept)
    runner.seed_report = {"loaded": len(seeds), "usable": len(kept), "dropped": dropped}
    print(f"stress run: engine {engine.version} ({engine.sha256[:12]}), {len(kept)} seeds, modes {','.join(cfg.modes)}, {cfg.workers} workers, budget {cfg.seconds/3600:.2f} h, seed {cfg.master_seed!r}", flush=True)
    try:
        runner.run()
    except KeyboardInterrupt:
        print("interrupted — writing what we have", flush=True)
    runner.perf_confirmed = runner.remeasure_perf()
    runner.checkpoint(final=True)
    summary = R.summarise(runner, final=True)
    print(R.one_line(summary), flush=True)
    return 0
