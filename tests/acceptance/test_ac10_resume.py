"""AC-10 (R6): a killed run restarted with the same run dir skips completed trials and ends with
exactly configs x docs x trials records, no duplicates.

Runner contract: injbench.runner.run_trials(run_dir, defenses, docs, profiles, trials) iterates
config -> doc -> trial, appends one JSONL line per trial to run_dir/records.jsonl and flushes it.
A kill can leave a half-written last line; the restart must not keep or build on it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from acceptance_support import make_doc, make_profile, make_record, read_jsonl

CONFIGS = ("a", "d")
TRIALS = 3


class FakeDefense:
    def __init__(self, config: str, calls: list[str], kill_on_call: int | None = None) -> None:
        self.config = config
        self.calls = calls
        self.kill_on_call = kill_on_call

    def run(self, doc: Any, profile: Any, trial: int) -> Any:
        self.calls.append(f"{self.config}|{doc.doc_id}|{trial}")
        if self.kill_on_call is not None and len(self.calls) == self.kill_on_call:
            raise KeyboardInterrupt
        return make_record(self.config, doc.doc_id, trial)


def _setup() -> tuple[list[Any], dict[str, Any]]:
    docs = [make_doc(f"r-{i}") for i in range(3)]
    return docs, {"prof-test-01": make_profile()}


def _records(run_dir: Path) -> list[Any]:
    from injbench.schema import RunRecord

    return [RunRecord.model_validate_json(x) for x in read_jsonl(run_dir / "records.jsonl")]


def test_killed_run_resumes_without_duplicates(tmp_path: Path) -> None:
    from injbench.runner import run_trials

    docs, profiles = _setup()
    total = len(CONFIGS) * len(docs) * TRIALS
    run_dir = tmp_path / "results" / "resume"

    calls: list[str] = []
    killer = {c: FakeDefense(c, calls, kill_on_call=8) for c in CONFIGS}
    with pytest.raises(KeyboardInterrupt):
        run_trials(run_dir, killer, docs, profiles, TRIALS)
    done = _records(run_dir)
    assert len(done) == 7, "each finished trial must be flushed before the next starts"

    with (run_dir / "records.jsonl").open("a", encoding="utf-8") as f:
        f.write('{"key": "d|r-2|1", "config": "d", "doc_')  # killed mid-write

    calls = []
    run_trials(run_dir, {c: FakeDefense(c, calls) for c in CONFIGS}, docs, profiles, TRIALS)
    assert len(calls) == total - len(done), "completed trials must be skipped"

    records = _records(run_dir)  # every line must parse: no partial line left behind
    keys = [r.key for r in records]
    assert len(records) == total
    assert len(set(keys)) == total
    per_cell: dict[tuple[str, str], set[int]] = {}
    for r in records:
        per_cell.setdefault((r.config, r.doc_id), set()).add(r.trial)
    assert len(per_cell) == len(CONFIGS) * len(docs)
    assert all(len(trials) == TRIALS for trials in per_cell.values())


def test_rerun_of_complete_run_does_nothing(tmp_path: Path) -> None:
    from injbench.runner import run_trials

    docs, profiles = _setup()
    run_dir = tmp_path / "results" / "complete"
    run_trials(run_dir, {c: FakeDefense(c, []) for c in CONFIGS}, docs, profiles, TRIALS)
    before = (run_dir / "records.jsonl").read_bytes()

    calls: list[str] = []
    run_trials(run_dir, {c: FakeDefense(c, calls) for c in CONFIGS}, docs, profiles, TRIALS)
    assert calls == []
    assert (run_dir / "records.jsonl").read_bytes() == before
