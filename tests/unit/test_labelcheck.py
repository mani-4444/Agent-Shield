import csv
import json
from pathlib import Path

import pytest
from test_metrics import fake_run
from typer.testing import CliRunner

from injbench.cli import app
from injbench.data.generate import build_dataset
from injbench.labelcheck import SHEET_COLUMNS, read_sheet, sample_for_labelling, write_sheet

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def parts() -> tuple:
    ds = build_dataset(2026)
    return fake_run(ds, "abcde", trials=3, split="dev"), {d.doc_id: d for d in ds.dev}


def test_sheet_is_blind_and_round_trips(tmp_path: Path, parts: tuple) -> None:
    records, docs = parts
    sample = sample_for_labelling(records, docs, n=60)
    assert "attack_success" not in SHEET_COLUMNS and "detector" not in " ".join(SHEET_COLUMNS)
    sheet = tmp_path / "s.csv"
    write_sheet(sheet, sample, docs)
    rows = list(csv.DictReader(sheet.open(encoding="utf-8", newline="")))
    assert len(rows) == 60 and all(r["human_attack_success"] == "" for r in rows)
    for i, r in enumerate(rows):
        r["human_attack_success"] = "yes" if i % 2 else "no"
    with sheet.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    labels = read_sheet(sheet)
    assert len(labels) == 60 and sum(labels.values()) == 30


def test_blank_label_is_rejected(tmp_path: Path, parts: tuple) -> None:
    records, docs = parts
    sheet = tmp_path / "s.csv"
    write_sheet(sheet, sample_for_labelling(records, docs, n=3), docs)
    with pytest.raises(ValueError):
        read_sheet(sheet)


def test_small_strata_are_topped_up(parts: tuple) -> None:
    records, docs = parts
    one_config = [r for r in records if r.config == "a"]
    sample = sample_for_labelling(one_config, docs, n=60)  # 3 strata, plenty of trials
    assert len(sample) == 60
    few = [r for r in one_config if r.trial == 0][:12]
    assert len(sample_for_labelling(few, docs, n=60)) == len(
        [r for r in few if docs[r.doc_id].attack]
    )


def test_cli_sample_then_score(
    tmp_path: Path, parts: tuple, monkeypatch: pytest.MonkeyPatch
) -> None:
    records, _ = parts
    run = tmp_path / "run"
    run.mkdir()
    (run / "records.jsonl").write_text(
        "".join(r.model_dump_json() + "\n" for r in records), encoding="utf-8"
    )
    (run / "run_config.json").write_text(
        json.dumps({"data_dir": str(ROOT / "data" / "v1")}), encoding="utf-8"
    )
    monkeypatch.chdir(ROOT)
    assert CliRunner().invoke(app, ["label-sample", "--run", str(run)]).exit_code == 0
    sheet = run / "label_sheet.csv"
    rows = list(csv.DictReader(sheet.open(encoding="utf-8", newline="")))
    for r in rows:
        r["human_attack_success"] = "yes" if r["decision"] == "APPROVE" else "no"
    with sheet.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    result = CliRunner().invoke(app, ["label-score", "--run", str(run)])
    assert result.exit_code == 0, result.output
    text = (run / "label_check.md").read_text(encoding="utf-8")
    assert "Agreement:" in text and "## Disagreements" in text
