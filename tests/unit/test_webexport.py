import csv
import json
from pathlib import Path

import pytest
from test_metrics import fake_run

from injbench import detectors
from injbench.data.generate import build_dataset
from injbench.metrics import summarize
from injbench.report import load_run, summary_csv
from injbench.webexport import FAMILY_NAMES, PLAIN_NAMES, build_trials, export_web

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
    site = ROOT / "web" / "src" / "data" / "results.json"
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


def test_trials_cover_every_record_with_metric_detectors(run_dir: Path, tmp_path: Path) -> None:
    export_web(run_dir, tmp_path)
    trials = json.loads((tmp_path / "trials.json").read_text(encoding="utf-8"))
    records, docs, profiles = load_run(run_dir)
    assert sum(len(ts) for d in trials for ts in d["trials"].values()) == len(records)
    assert [d["doc_id"] for d in trials] == sorted({r.doc_id for r in records})
    by_key = {r.key: r for r in records}
    for d in trials:
        doc = docs[d["doc_id"]]
        p = profiles[doc.profile_id]
        assert (d["family"] is None) == (doc.attack is None)
        for config, ts in d["trials"].items():
            for i, t in enumerate(ts):
                r = by_key[f"{config}|{d['doc_id']}|{i}"]
                assert t["correct"] == detectors.decision_correct(r, doc, p)
                expected = detectors.attack_success(r, doc, p) if doc.attack else None
                assert t["attack_worked"] == expected
                assert t["text"]


def test_build_trials_is_sorted(run_dir: Path) -> None:
    records, docs, profiles = load_run(run_dir)
    out = build_trials(list(reversed(records)), docs, profiles)
    assert [d.doc_id for d in out] == sorted(d.doc_id for d in out)
    assert all(list(d.trials) == sorted(d.trials) for d in out)


def test_committed_trials_match_main_summary() -> None:
    """Rates recomputed from the shipped trials.json equal summary.csv (same detectors)."""
    site = ROOT / "web" / "src" / "data" / "trials.json"
    summary = ROOT / "results" / "v1-main" / "summary.csv"
    if not site.is_file() or not summary.is_file():
        pytest.skip("site trials or main summary not present")
    docs = json.loads(site.read_text(encoding="utf-8"))
    with summary.open(encoding="utf-8", newline="") as f:
        rows = {r["config"]: r for r in csv.DictReader(f) if r["group"] == "all"}
    for config, row in rows.items():
        # asr_mean and benign_accuracy are means over docs of per-doc trial means;
        # summary.csv rounds to 6 decimals
        attack = [d["trials"][config] for d in docs if d["family"] and config in d["trials"]]
        normal = [d["trials"][config] for d in docs if not d["family"] and config in d["trials"]]
        asr = sum(sum(t["attack_worked"] for t in ts) / len(ts) for ts in attack) / len(attack)
        acc = sum(sum(t["correct"] for t in ts) / len(ts) for ts in normal) / len(normal)
        assert asr == pytest.approx(float(row["asr_mean_value"]), abs=5e-7), config
        assert acc == pytest.approx(float(row["benign_accuracy_value"]), abs=5e-7), config
