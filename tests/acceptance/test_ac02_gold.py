"""AC-2 (R1): benign gold == decide(gold, profile); >=25% Telugu/code-mixed; each decision >=20.

Split sizes come from R1: test = 200 benign, dev = 30 benign.
"""

from __future__ import annotations

from collections import Counter

from acceptance_support import DECISIONS, Dataset


def test_benign_split_sizes(dataset: Dataset) -> None:
    assert sum(d.attack is None for d in dataset.test) == 200
    assert sum(d.attack is None for d in dataset.dev) == 30
    assert all(d.split == "test" for d in dataset.test)
    assert all(d.split == "dev" for d in dataset.dev)


def test_doc_ids_unique_and_profiles_resolve(dataset: Dataset) -> None:
    ids = [d.doc_id for d in dataset.docs]
    assert len(ids) == len(set(ids))
    assert all(d.profile_id in dataset.profiles for d in dataset.docs)


def test_benign_gold_matches_engine(dataset: Dataset) -> None:
    from injbench.agent.engine import decide

    wrong = []
    for d in dataset.docs:
        if d.attack is None:
            decision, _tools = decide(d.gold, dataset.profiles[d.profile_id])
            if decision != d.gold_decision:
                wrong.append((d.doc_id, d.gold_decision, decision))
    assert not wrong, f"gold_decision != decide(): {wrong[:5]}"


def test_telugu_share_at_least_25_percent(dataset: Dataset) -> None:
    benign = [d for d in dataset.test if d.attack is None]
    telugu = sum(d.lang in ("te", "te-en") for d in benign)
    assert telugu / len(benign) >= 0.25, f"{telugu}/{len(benign)} Telugu or code-mixed"


def test_each_decision_appears_20_times(dataset: Dataset) -> None:
    counts = Counter(d.gold_decision for d in dataset.test if d.attack is None)
    short = {k: counts.get(k, 0) for k in DECISIONS if counts.get(k, 0) < 20}
    assert not short, f"decisions under 20: {short} (all: {dict(counts)})"
