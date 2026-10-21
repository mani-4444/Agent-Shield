import math
import time

import numpy as np
import pytest

from injbench import metrics
from injbench.data.generate import Dataset, build_dataset
from injbench.metrics import HEADLINE, RatioMetric, bootstrap_ci, summarize
from injbench.rng import make_rng
from injbench.schema import Document, RunRecord, ToolCall


@pytest.fixture(scope="module")
def ds() -> Dataset:
    return build_dataset(2026)


def fake_run(
    ds: Dataset, configs: str = "abcde", trials: int = 3, split: str = "test"
) -> list[RunRecord]:
    """Synthetic records: each config approves poisoned docs with its own probability."""
    docs = ds.test if split == "test" else ds.dev
    out = []
    for ci, c in enumerate(configs):
        rng = make_rng(1, "fake_run", c)
        for d in docs:
            for t in range(trials):
                attacked = d.attack is not None and rng.random() < 0.5 / (ci + 1)
                decision = "APPROVE" if attacked else d.gold_decision
                calls = []
                if decision == "APPROVE":
                    payee = d.attack.attacker_vpa if attacked and d.attack else d.gold.payee_vpa
                    calls = [
                        ToolCall(
                            name="approve_payment",
                            args={
                                "payee_vpa": payee or "x@fakepay",
                                "amount_inr": d.gold.amount_inr,
                            },
                        )
                    ]
                blocked = c in "ce" and rng.random() < 0.1
                out.append(
                    RunRecord(
                        key=f"{c}|{d.doc_id}|{t}",
                        config=c,
                        doc_id=d.doc_id,
                        trial=t,
                        model_id="m",
                        git_sha="s",
                        decision="FLAG" if blocked else decision,
                        tool_calls=[] if blocked else calls,  # type: ignore[arg-type]
                        user_message="",
                        raw_output="",
                        extracted=None,
                        classifier_score=0.9 if blocked else 0.1,
                        blocked_by_classifier=blocked,
                        latency_ms={"total": float(100 + 10 * ci + rng.integers(0, 50))},
                        tokens={"prompt": int(rng.integers(100, 200))},
                        error=None,
                        cache_hit=False,
                    )
                )
    return out


def naive_bootstrap(
    metric: RatioMetric,
    records: list[RunRecord],
    docs: dict[str, Document],
    profiles: dict,
    n_boot: int,
    seed: int,
) -> tuple[float, float]:
    """Slow reference: re-score relabelled copies of the drawn documents' records."""
    ids, _ = metric.per_doc(records, docs, profiles)
    by_doc: dict[str, list[RunRecord]] = {}
    for r in records:
        by_doc.setdefault(r.doc_id, []).append(r)
    rng = make_rng(seed, "bootstrap")
    stats = []
    for row in rng.integers(0, len(ids), size=(n_boot, len(ids))):
        recs, alias = [], dict(docs)
        for j, i in enumerate(row):
            new_id = f"{ids[i]}#{j}"
            alias[new_id] = docs[ids[i]]
            recs += [r.model_copy(update={"doc_id": new_id}) for r in by_doc[ids[i]]]
        stats.append(metric(recs, alias, profiles))
    lo, hi = np.nanpercentile(stats, [2.5, 97.5])
    return float(lo), float(hi)


@pytest.mark.parametrize("name", ["asr_mean", "asr_worst", "utility_safe", "benign_accuracy"])
def test_fast_bootstrap_matches_naive_reference(ds: Dataset, name: str) -> None:
    records = [r for r in fake_run(ds, "a", split="dev")]
    docs = {d.doc_id: d for d in ds.dev}
    profiles = {p.profile_id: p for p in ds.profiles}
    metric = getattr(metrics, name)
    fast = bootstrap_ci(metric, records, docs, profiles, n_boot=200, seed=5)
    slow = naive_bootstrap(metric, records, docs, profiles, n_boot=200, seed=5)
    assert fast == pytest.approx(slow)


def test_empty_inputs_give_nan(ds: Dataset) -> None:
    docs = {d.doc_id: d for d in ds.dev}
    profiles = {p.profile_id: p for p in ds.profiles}
    assert math.isnan(metrics.asr_mean([], docs, profiles))
    assert all(math.isnan(x) for x in bootstrap_ci(metrics.asr_mean, [], docs, profiles))
    benign_only = [r for r in fake_run(ds, "a", split="dev") if docs[r.doc_id].attack is None]
    assert math.isnan(metrics.asr_mean(benign_only, docs, profiles))


def test_summarize_rows_and_delta_latency(ds: Dataset) -> None:
    records = fake_run(ds, "ad", trials=1, split="dev")
    docs = {d.doc_id: d for d in ds.dev}
    profiles = {p.profile_id: p for p in ds.profiles}
    rows = summarize(records, docs, profiles, n_boot=100)
    headline = [r for r in rows if r.group == "all"]
    assert [r.config for r in headline] == ["a", "d"]
    assert headline[0].metrics["delta_latency_p50"].value == 0.0
    assert set(headline[0].metrics) == {m.name for m in HEADLINE} | {"delta_latency_p50"}
    groups = {r.group.split("=")[0] for r in rows if r.group != "all"}
    assert groups == {"family", "goal", "lang"}
    assert all(
        set(r.metrics)
        == {
            "asr_mean",
            "asr_worst",
            "any_deviation_rate",
            "utility_strict",
            "utility_safe",
            "asr_twin_adjusted",
        }
        for r in rows
        if r.group != "all"
    )
    assert summarize(records, docs, profiles, n_boot=100) == rows  # deterministic


def test_full_scale_summary_is_fast(ds: Dataset) -> None:
    records = fake_run(ds)  # 5 configs x 400 docs x 3 trials = 6,000 records
    docs = {d.doc_id: d for d in ds.test}
    profiles = {p.profile_id: p for p in ds.profiles}
    start = time.perf_counter()
    rows = summarize(records, docs, profiles)
    assert time.perf_counter() - start < 120
    a = next(r for r in rows if r.config == "a" and r.group == "all").metrics["asr_mean"]
    e = next(r for r in rows if r.config == "e" and r.group == "all").metrics["asr_mean"]
    assert a.value is not None and e.value is not None and a.value > e.value
    assert a.lo is not None and a.hi is not None and a.lo <= a.value <= a.hi
    assert a.n_docs == 200


def _pair_records(
    twin_approves: bool, with_twin: bool = True
) -> tuple[list[RunRecord], dict, dict]:
    ds = build_dataset(2026)
    poisoned = next(d for d in ds.dev if d.attack and d.attack.goal == "G1_force_approve")
    twin = next(d for d in ds.dev if d.doc_id == poisoned.twin_id)
    docs = {poisoned.doc_id: poisoned, twin.doc_id: twin}
    profiles = {p.profile_id: p for p in ds.profiles}

    def rec(d: Document, decision: str) -> RunRecord:
        return RunRecord(
            key=f"a|{d.doc_id}|0",
            config="a",
            doc_id=d.doc_id,
            trial=0,
            model_id="m",
            git_sha="s",
            decision=decision,
            tool_calls=[],
            user_message="",
            raw_output="",
            extracted=None,  # type: ignore[arg-type]
            classifier_score=None,
            blocked_by_classifier=False,
            latency_ms={"total": 1.0},
            tokens={},
            error=None,
            cache_hit=False,
        )

    records = [rec(poisoned, "APPROVE")]
    if with_twin:
        records.append(rec(twin, "APPROVE" if twin_approves else twin.gold_decision))
    return records, docs, profiles


def test_twin_adjusted_drops_successes_the_twin_already_shows() -> None:
    records, docs, profiles = _pair_records(twin_approves=True)
    assert metrics.asr_mean(records, docs, profiles) == 1.0
    assert metrics.asr_twin_adjusted(records, docs, profiles) == 0.0


def test_twin_adjusted_keeps_attack_caused_successes() -> None:
    records, docs, profiles = _pair_records(twin_approves=False)
    assert metrics.asr_twin_adjusted(records, docs, profiles) == 1.0


def test_twin_adjusted_without_twin_is_unadjusted() -> None:
    records, docs, profiles = _pair_records(twin_approves=True, with_twin=False)
    assert metrics.asr_twin_adjusted(records, docs, profiles) == 1.0


def test_group_rows_see_the_twins() -> None:
    records, docs, profiles = _pair_records(twin_approves=True)
    rows = summarize(records, docs, profiles, n_boot=20)
    family_rows = [r for r in rows if r.group.startswith("family=")]
    assert family_rows and all(r.metrics["asr_twin_adjusted"].value == 0.0 for r in family_rows)
    assert all(r.metrics["asr_mean"].value == 1.0 for r in family_rows)
