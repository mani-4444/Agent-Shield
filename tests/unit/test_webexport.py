import csv
import json
from pathlib import Path

import pytest
from test_metrics import fake_run

from injbench.data.generate import build_dataset
from injbench.metrics import summarize
from injbench.report import summary_csv
from injbench.webexport import FAMILY_NAMES, PLAIN_NAMES, export_web

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def run_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    ds = build_dataset(2026)
    records = fake_run(ds, "abcde", trials=1, split="dev")
    docs = {d.doc_id: d for d in ds.dev}
    profiles = {p.profile_id: p for p in ds.profiles}
    run = tmp_path_factory.mktemp("run")
    (run / "records.jsonl").write_text(
        "".join(r.model_dump_json() + "\n" for r in records), encoding="utf-8"
    )
    (run / "summary.csv").write_text(
        summary_csv(summarize(records, docs, profiles, n_boot=50)), encoding="utf-8"
    )
    (run / "run_config.json").write_text(
        json.dumps({"data_dir": str(ROOT / "data" / "v1"), "threshold_override": 0.5}),
        encoding="utf-8",
    )
    return run


def test_results_numbers_are_copied_from_summary_csv(run_dir: Path, tmp_path: Path) -> None:
    export_web(run_dir, tmp_path, run_date="2026-10-22")
    data = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    with (run_dir / "summary.csv").open(encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))
    assert len(data["rows"]) == len(csv_rows)
    for row, src in zip(data["rows"], csv_rows, strict=True):
        assert (row["config"], row["group"]) == (src["config"], src["group"])
        for metric, cell in row["metrics"].items():
            expected = src[f"{metric}_value"]
            assert cell["value"] == (None if expected == "" else float(expected)), (
                row["config"],
                metric,
            )
    assert data["n_records"] == 60 * 5 and data["trials"] == 1 and data["threshold"] == 0.5
    assert data["run_date"] == "2026-10-22"
    assert {r["name"] for r in data["rows"]} == set(PLAIN_NAMES.values())


def test_examples_are_real_and_plain(run_dir: Path, tmp_path: Path) -> None:
    export_web(run_dir, tmp_path)
    examples = json.loads((tmp_path / "examples.json").read_text(encoding="utf-8"))
    assert examples, "fake_run should produce at least one (a)-fooled, (d)-safe case"
    assert len({e["family"] for e in examples}) == len(examples)  # at most one per family
    for e in examples:
        assert e["family_name"] == FAMILY_NAMES[e["family"]]
        assert e["hidden_instruction"] and e["hidden_instruction"] in e["message"]
        assert e["actions"]["a"]["attack_succeeded"] and not e["actions"]["d"]["attack_succeeded"]
        assert all(a["text"] for a in e["actions"].values())
        assert chr(0x200B) not in e["message"]


def test_export_is_deterministic(run_dir: Path, tmp_path: Path) -> None:
    first = [p.read_bytes() for p in export_web(run_dir, tmp_path / "one")]
    second = [p.read_bytes() for p in export_web(run_dir, tmp_path / "two")]
    assert first == second


def test_committed_site_data_matches_main_summary() -> None:
    """The JSON shipped with the site must equal results/v1-main/summary.csv (no hand edits)."""
    site = ROOT / "web" / "public" / "data" / "results.json"
    summary = ROOT / "results" / "v1-main" / "summary.csv"
    if not site.is_file() or not summary.is_file():
        pytest.skip("site data or main summary not present")
    data = json.loads(site.read_text(encoding="utf-8"))
    with summary.open(encoding="utf-8", newline="") as f:
        csv_rows = {(r["config"], r["group"]): r for r in csv.DictReader(f)}
    for row in data["rows"]:
        src = csv_rows[(row["config"], row["group"])]
        for metric, cell in row["metrics"].items():
            expected = src[f"{metric}_value"]
            assert cell["value"] == (None if expected == "" else float(expected))
