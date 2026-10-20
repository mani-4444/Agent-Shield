import unicodedata
from collections import Counter

import pytest

from injbench.agent.engine import remaining_budget
from injbench.data.generate import (
    LANG_PLAN,
    PLAN,
    Dataset,
    build_dataset,
    format_inr,
    generate_profiles,
)
from injbench.schema import VPA_RE


@pytest.fixture(scope="module")
def ds() -> Dataset:
    return build_dataset(2026)


@pytest.mark.parametrize(
    ("n", "s"),
    [(0, "0"), (999, "999"), (1000, "1,000"), (120000, "1,20,000"), (12345678, "1,23,45,678")],
)
def test_format_inr_indian_grouping(n: int, s: str) -> None:
    assert format_inr(n) == s


def test_profiles_are_plausible_and_synthetic() -> None:
    profiles = generate_profiles(2026)
    assert len(profiles) == 20
    assert len({p.profile_id for p in profiles}) == 20
    for p in profiles:
        assert 15000 <= p.monthly_budget_inr <= 80000
        assert remaining_budget(p) >= 0.15 * p.monthly_budget_inr - 100
        assert 2 <= len(p.trusted_payees) <= 4
        assert all(VPA_RE.fullmatch(v) for v in p.trusted_payees)
        assert all(v.endswith(("@fakepay", "@examplebank")) for v in p.trusted_payees)
        assert 5000 <= p.large_txn_threshold_inr <= 25000
        assert p.canary_account_no.startswith("CANARY-")


def test_plan_counts_are_exact(ds: Dataset) -> None:
    for split, docs in (("test", ds.test), ("dev", ds.dev)):
        benign = [d for d in docs if d.attack is None]
        got = Counter((d.gold.intent, d.gold_decision) for d in benign)
        assert dict(got) == PLAN[split]  # type: ignore[index]
        assert dict(Counter(d.lang for d in benign)) == LANG_PLAN[split]  # type: ignore[index]


def test_text_carries_the_gold_facts(ds: Dataset) -> None:
    for d in ds.test + ds.dev:
        if d.attack is not None:
            continue
        assert format_inr(d.gold.amount_inr) in d.ocr_text, d.doc_id
        if d.gold.payee_vpa:
            assert d.gold.payee_vpa in d.ocr_text, d.doc_id
            assert VPA_RE.fullmatch(d.gold.payee_vpa), d.doc_id
        if d.doc_type == "receipt_ocr":
            assert (d.gold.merchant or "").upper() in d.ocr_text, d.doc_id


def test_doc_types_match_intents(ds: Dataset) -> None:
    for d in ds.test + ds.dev:
        expected = {
            "debit_alert": {"bank_sms"},
            "receipt": {"receipt_ocr"},
            "payment_request": {"bank_sms", "chat_message"},
        }[d.gold.intent]
        assert d.doc_type in expected, d.doc_id


def test_text_is_nfc_normalised(ds: Dataset) -> None:
    for d in ds.test + ds.dev:
        assert unicodedata.normalize("NFC", d.ocr_text) == d.ocr_text, d.doc_id


def test_telugu_docs_contain_telugu_script(ds: Dataset) -> None:
    for d in (d for d in ds.test + ds.dev if d.attack is None):  # F4 twins add Telugu payloads
        has_telugu = any("\u0c00" <= ch <= "\u0c7f" for ch in d.ocr_text)
        assert has_telugu == (d.lang == "te"), d.doc_id


def test_dev_and_test_differ(ds: Dataset) -> None:
    assert not {d.ocr_text for d in ds.test} & {d.ocr_text for d in ds.dev}


def test_seed_changes_everything() -> None:
    a, b = build_dataset(2026), build_dataset(7)
    assert [d.ocr_text for d in a.test] != [d.ocr_text for d in b.test]
    assert [p.canary_account_no for p in a.profiles] != [p.canary_account_no for p in b.profiles]
