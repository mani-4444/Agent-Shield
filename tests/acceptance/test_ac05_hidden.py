"""AC-5 (R2, F3): hidden-text payloads are in ocr_text but not visible_text.

DESIGN.md §3: ocr_text == visible_text for every doc except F3.
"""

from __future__ import annotations

from acceptance_support import Dataset, nfc


def test_hidden_payload_only_in_ocr_layer(dataset: Dataset) -> None:
    hidden = [d for d in dataset.docs if d.attack and d.attack.family == "F3_hidden"]
    assert hidden, "no F3 docs generated"
    for d in hidden:
        payload = nfc(d.attack.payload)
        assert payload in nfc(d.ocr_text), d.doc_id
        assert payload not in nfc(d.visible_text), d.doc_id


def test_non_hidden_docs_have_identical_layers(dataset: Dataset) -> None:
    for d in dataset.docs:
        if not (d.attack and d.attack.family == "F3_hidden"):
            assert d.ocr_text == d.visible_text, d.doc_id
