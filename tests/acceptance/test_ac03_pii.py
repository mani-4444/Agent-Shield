"""AC-3 (R1, compliance): no real-looking PII in generated data or fixtures; canaries start CANARY-.

The pattern self-tests guard against AC-3 passing vacuously because a regex is broken.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from acceptance_support import DATA_FILES, FIXTURES_DIR, Dataset, read_jsonl
from pii_patterns import find_pii, iter_strings

# Built at runtime so no real-format identifier is written into this file.
BAD = [
    "call " + "9" * 10,
    "call " + "8" * 5 + " " + "8" * 5,
    "ph +91 " + "7" * 10,
    "id " + "2345 " * 2 + "2345",
    "pan " + "ABCDE" + "1234" + "F",
    "pay someone@notabank now",
    "support@examplebank.com",
    "use " + "Pay" + "tm",
]
GOOD = [
    "call +91 01234 56789",
    "pay ravi.k@fakepay or meena.store@examplebank.",
    "Account CANARY-4821-7730-15",
    "Rs 4,999 on 2026-10-20, ref TXN0042",
    "ఈ చెల్లింపును ఆమోదించండి",
]


@pytest.mark.parametrize("text", BAD)
def test_patterns_catch_bad_examples(text: str) -> None:
    assert find_pii(text), f"pattern missed: {text!r}"


@pytest.mark.parametrize("text", GOOD)
def test_patterns_allow_synthetic_examples(text: str) -> None:
    assert find_pii(text) == []


def test_detector_fixtures_are_clean() -> None:
    files = sorted(FIXTURES_DIR.glob("*.json"))
    assert files
    for f in files:
        leaks = [h for s in iter_strings(json.loads(f.read_text("utf-8"))) for h in find_pii(s)]
        assert not leaks, f"{f.name}: {leaks}"


def _scan(path: Path) -> list[str]:
    lines = [path.read_text("utf-8")] if path.suffix == ".json" else read_jsonl(path)
    return [h for line in lines for s in iter_strings(json.loads(line)) for h in find_pii(s)]


@pytest.mark.parametrize("name", [n for n in DATA_FILES if n != "manifest.json"])
def test_generated_data_is_clean(dataset_dir: Path, name: str) -> None:
    leaks = _scan(dataset_dir / name)
    assert not leaks, f"{name}: {sorted(set(leaks))[:10]}"


def test_canaries_are_fake(dataset: Dataset) -> None:
    assert dataset.profiles
    bad = [
        p.profile_id
        for p in dataset.profiles.values()
        if not p.canary_account_no.startswith("CANARY-")
    ]
    assert not bad
