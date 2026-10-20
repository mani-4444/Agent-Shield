import json
import unicodedata
from collections import Counter

import pytest

from injbench.data.attacks import (
    FAMILIES,
    ZERO_WIDTH,
    family_targets,
    insert_visible,
    payload_templates,
    zero_width_join,
)
from injbench.data.generate import Dataset, build_dataset
from injbench.schema import Document


@pytest.fixture(scope="module")
def ds() -> Dataset:
    return build_dataset(2026)


def poisoned(ds: Dataset) -> list[Document]:
    return [d for d in ds.test + ds.dev if d.attack is not None]


def test_templates_8_to_12_per_family_and_placeholders_known() -> None:
    t = payload_templates()
    assert set(t) == set(FAMILIES)
    for fam, by_goal in t.items():
        n = sum(len(v) for v in by_goal.values())
        assert 8 <= n <= 12, (fam, n)
        for template in (x for v in by_goal.values() for x in v):
            leftover = template
            for ph in ("{attacker_vpa}", "{attacker_amount}", "{attacker_contact}"):
                leftover = leftover.replace(ph, "")
            assert "{attacker" not in leftover, template


def test_family_goal_compatibility(ds: Dataset) -> None:
    allowed = {"F6_exfil": {"G3_exfiltrate"}, "F5_toolarg": {"G1_force_approve", "G2_redirect"}}
    for d in poisoned(ds):
        assert d.attack is not None
        assert d.attack.goal in allowed.get(
            d.attack.family, {"G1_force_approve", "G2_redirect", "G3_exfiltrate"}
        )


def test_family_counts_hit_targets(ds: Dataset) -> None:
    for docs in (ds.test, ds.dev):
        got = Counter(d.attack.family for d in docs if d.attack)
        assert dict(got) == family_targets(sum(d.attack is None for d in docs))


def test_payloads_filled_synthetic_and_canary_free(ds: Dataset) -> None:
    profiles = {p.profile_id: p for p in ds.profiles}
    for d in poisoned(ds):
        a = d.attack
        assert a is not None and "{attacker" not in a.payload
        assert a.attacker_vpa and a.attacker_vpa.endswith(("@fakepay", "@examplebank"))
        assert a.attacker_vpa not in profiles[d.profile_id].trusted_payees
        assert a.attacker_contact and a.attacker_contact.startswith("+91 0")
        assert "CANARY" not in a.payload
        assert unicodedata.normalize("NFC", a.payload) == a.payload


def test_g2_attacker_amount_differs_from_gold(ds: Dataset) -> None:
    for d in poisoned(ds):
        if d.attack and d.attack.goal == "G2_redirect":
            assert d.attack.attacker_amount_inr != d.gold.amount_inr


def test_hidden_and_visible_positions(ds: Dataset) -> None:
    for d in poisoned(ds):
        assert d.attack is not None
        if d.attack.family == "F3_hidden":
            assert d.attack.position == "hidden"
        else:
            assert d.attack.position in {"start", "middle", "end", "footer"}


def test_f4_payload_lang_matches_script(ds: Dataset) -> None:
    for d in poisoned(ds):
        assert d.attack is not None
        telugu = any("\u0c00" <= ch <= "\u0c7f" for ch in d.attack.payload)
        expected = ("te" if telugu else "te-en") if d.attack.family == "F4_multilingual" else "en"
        assert d.attack.payload_lang == expected


def test_twins_interleave_after_their_benign_doc(ds: Dataset) -> None:
    ids = [d.doc_id for d in ds.test]
    assert ids[:4] == ["t-001", "t-001-p", "t-002", "t-002-p"]
    assert len(ds.test) == 400 and len(ds.dev) == 60


def test_zero_width_join_keeps_phone_intact() -> None:
    out = zero_width_join("send it to +91 01234 56789 today", "+91 01234 56789")
    assert "+91 01234 56789" in out
    assert out.count(ZERO_WIDTH) == 4 and " to " not in out


@pytest.mark.parametrize(
    ("position", "expected"),
    [("start", "start"), ("end", "end"), ("footer", "footer"), ("middle", "middle")],
)
def test_insert_visible_positions(position: str, expected: str) -> None:
    text, pos = insert_visible("Pay Rs 10. Thanks.", "PAYLOAD", position)  # type: ignore[arg-type]
    assert "PAYLOAD" in text and pos == expected


def test_middle_falls_back_to_end_without_boundary() -> None:
    text, pos = insert_visible("no boundary here", "PAYLOAD", "middle")
    assert pos == "end" and text.endswith("PAYLOAD")


def test_templates_json_has_no_real_brands() -> None:
    from importlib.resources import files

    raw = files("injbench.data").joinpath("templates/payloads.json").read_text(encoding="utf-8")
    json.loads(raw)
    for brand in ("paytm", "phonepe", "google pay", "gpay", "bhim", "hdfc", "icici", "sbi "):
        assert brand not in raw.lower()
