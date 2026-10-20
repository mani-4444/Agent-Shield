import csv
import io
import json
from pathlib import Path

import pytest
from test_metrics import fake_run

from injbench.data.generate import build_dataset
from injbench.metrics import summarize
from injbench.report import _cell, gallery_md, spread_labels, summary_csv, write_report
from injbench.schema import MetricValue


@pytest.fixture(scope="module")
def run_parts() -> tuple:
    ds = build_dataset(2026)
    records = fake_run(ds, "ad", trials=1, split="dev")
    docs = {d.doc_id: d for d in ds.dev}
    profiles = {p.profile_id: p for p in ds.profiles}
    return records, docs, profiles


def test_summary_csv_is_deterministic_with_config_column(run_parts: tuple) -> None:
    records, docs, profiles = run_parts
    a = summary_csv(summarize(records, docs, profiles, n_boot=50))
    b = summary_csv(summarize(records, docs, profiles, n_boot=50))
    assert a == b and "\r" not in a
    rows = list(csv.DictReader(io.StringIO(a)))
    assert {r["config"] for r in rows} == {"a", "d"}
    assert (
        rows[0]["group"] == "all" and "asr_mean_value" in rows[0] and "asr_mean_n_docs" in rows[0]
    )


def test_cell_marks_low_n_and_formats_percent() -> None:
    assert (
        _cell(MetricValue(value=0.25, lo=0.2, hi=0.3, n_docs=10), True)
        == "25.0% [20.0, 30.0] (low n)"
    )
    assert _cell(MetricValue(value=12.0, lo=None, hi=None, n_docs=200), False) == "12"
    assert _cell(None, True) == "–"


def test_spread_labels_keeps_order_and_gap() -> None:
    placed = spread_labels([10.0, 10.5, 30.0, 10.2], 2.0)
    assert placed == [10.0, 14.0, 30.0, 12.0]


def test_gallery_ranks_attack_successes_first_and_escapes_zero_width(run_parts: tuple) -> None:
    records, docs, profiles = run_parts
    text = gallery_md(records, docs, profiles)
    for c in ("a", "d"):
        section = text.split(f"## Config {c}")[1].split("## Config")[0]
        heads = [line for line in section.splitlines() if line.startswith("### ")]
        assert 3 <= len(heads) <= 5
        kinds = [h.split(": ", 1)[1] for h in heads]
        order = ["attack succeeded", "wrong decision (poisoned)", "wrong decision (benign)"]
        assert [order.index(k) for k in kinds] == sorted(order.index(k) for k in kinds)
    assert "\u200b" not in text


def test_write_report_needs_records(tmp_path: Path) -> None:
    (tmp_path / "run_config.json").write_text(json.dumps({"data_dir": "data/v1"}), encoding="utf-8")
    with pytest.raises(ValueError):
        write_report(tmp_path)


def test_int_formatting_has_no_negative_zero() -> None:
    from injbench.report import _int

    assert _int(-0.3) == "0" and _int(12.6) == "13" and _int(-5.5) == "-6"


def test_classifier_fpr_is_na_without_a_classifier(run_parts: tuple, tmp_path: Path) -> None:
    from injbench.report import summary_md

    records, docs, profiles = run_parts
    no_clf = [r.model_copy(update={"classifier_score": None}) for r in records if r.config == "a"]
    text = summary_md(summarize(no_clf, docs, profiles, n_boot=20), no_clf, tmp_path)
    row = next(line for line in text.splitlines() if line.startswith("| (a) none"))
    assert "n/a" in row
