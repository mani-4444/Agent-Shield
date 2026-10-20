import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from injbench.agent import llm
from injbench.cli import app
from injbench.runner import RECORDS, load_records, run_trials
from injbench.schema import Document, GoldFacts, LLMRequest, LLMResponse, Profile, RunRecord

ROOT = Path(__file__).resolve().parents[2]
PROFILE = Profile(
    profile_id="p",
    monthly_budget_inr=20000,
    spent_this_month_inr=5000,
    trusted_payees=["ravi.k@fakepay"],
    large_txn_threshold_inr=10000,
    canary_account_no="CANARY-4821-7730-15",
)


def doc(i: int) -> Document:
    return Document(
        doc_id=f"x-{i}",
        split="dev",
        doc_type="receipt_ocr",
        lang="en",
        profile_id="p",
        visible_text="t",
        ocr_text="t",
        gold=GoldFacts(intent="receipt", payee_vpa=None, amount_inr=10, date=None, merchant=None),
        gold_decision="NO_ACTION",
        twin_id=None,
        attack=None,
    )


class Echo:
    name = "a"

    def __init__(self, config: str = "a", wrong_key: bool = False) -> None:
        self.config, self.wrong_key, self.calls = config, wrong_key, 0

    def run(self, d: Document, p: Profile, trial: int) -> RunRecord:
        self.calls += 1
        key = f"{self.config}|{d.doc_id}|{trial + 1 if self.wrong_key else trial}"
        return RunRecord(
            key=key,
            config=self.config,
            doc_id=d.doc_id,
            trial=trial + 1 if self.wrong_key else trial,
            model_id="m",
            git_sha="s",
            decision="NO_ACTION",
            tool_calls=[],
            user_message="",
            raw_output="",
            extracted=None,
            classifier_score=None,
            blocked_by_classifier=False,
            latency_ms={"total": 1.0},
            tokens={},
            error=None,
            cache_hit=True,
        )


def test_duplicates_and_garbage_are_repaired(tmp_path: Path) -> None:
    run_trials(tmp_path, {"a": Echo()}, [doc(1)], {"p": PROFILE}, 2)
    path = tmp_path / RECORDS
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([lines[0], lines[0], "garbage", lines[1]]) + "\n", encoding="utf-8")
    echo = Echo()
    records = run_trials(tmp_path, {"a": echo}, [doc(1)], {"p": PROFILE}, 2)
    assert echo.calls == 0 and len(records) == 2
    assert path.read_text(encoding="utf-8").splitlines() == lines


def test_key_mismatch_is_a_bug(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_trials(tmp_path, {"a": Echo(wrong_key=True)}, [doc(1)], {"p": PROFILE}, 1)


def test_progress_log_and_callback(tmp_path: Path) -> None:
    seen: list[tuple[int, int]] = []
    run_trials(
        tmp_path,
        {"a": Echo(), "d": Echo("d")},
        [doc(1), doc(2)],
        {"p": PROFILE},
        1,
        on_progress=lambda done, total, r: seen.append((done, total)),
    )
    assert seen == [(1, 4), (2, 4), (3, 4), (4, 4)]
    log = (tmp_path / "progress.log").read_text(encoding="utf-8").splitlines()
    assert len(log) == 4 and "4/4 d|x-2|0 cache_hits=4" in log[-1]
    assert [r.key for r in load_records(tmp_path / RECORDS)] == [
        "a|x-1|0",
        "a|x-2|0",
        "d|x-1|0",
        "d|x-2|0",
    ]


# --- eval CLI -----------------------------------------------------------------------------------


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    shutil.copytree(ROOT / "config", tmp_path / "config")
    monkeypatch.chdir(tmp_path)
    assert CliRunner().invoke(app, ["data", "--out", "data/v1"]).exit_code == 0
    calls: list[LLMRequest] = []

    def transport(req: LLMRequest) -> LLMResponse:
        calls.append(req)
        return LLMResponse(text="DECISION: NO_ACTION", tokens={"prompt": 1})

    monkeypatch.setattr(llm, "transport", transport)
    monkeypatch.setattr(llm, "_calls", calls, raising=False)
    yield tmp_path
    llm.configure(cache_dir=Path(".cache/llm"), replay=False)


def invoke(*args: str, input: str | None = None) -> Any:
    return CliRunner().invoke(app, list(args), input=input)


def test_eval_writes_records_and_run_config(workspace: Path) -> None:
    r = invoke(
        "eval",
        "--config",
        "a,d",
        "--split",
        "dev",
        "--trials",
        "2",
        "--limit",
        "3",
        "--run-id",
        "u1",
    )
    assert r.exit_code == 0, r.output
    run = workspace / "results" / "u1"
    assert len(load_records(run / RECORDS)) == 2 * 3 * 2
    cfg = json.loads((run / "run_config.json").read_text(encoding="utf-8"))
    assert cfg["configs"] == ["a", "d"] and cfg["limit"] == 3 and len(cfg["dataset_sha256"]) == 64
    assert "models:" in cfg["models_yaml"]


def test_eval_records_threshold_override(workspace: Path) -> None:
    args = ("eval", "--config", "a", "--split", "dev", "--trials", "1", "--limit", "1")
    assert invoke(*args, "--run-id", "t5", "--threshold", "0.5").exit_code == 0
    cfg = json.loads((workspace / "results" / "t5" / "run_config.json").read_text(encoding="utf-8"))
    assert cfg["threshold_override"] == 0.5


def test_eval_resume_makes_no_new_calls(workspace: Path) -> None:
    args = (
        "eval",
        "--config",
        "a",
        "--split",
        "dev",
        "--trials",
        "1",
        "--limit",
        "2",
        "--run-id",
        "u2",
    )
    assert invoke(*args).exit_code == 0
    before = len(llm._calls)  # type: ignore[attr-defined]
    assert invoke(*args).exit_code == 0
    assert len(llm._calls) == before  # type: ignore[attr-defined]


def test_eval_rejects_unknown_config(workspace: Path) -> None:
    assert invoke("eval", "--config", "a,z", "--run-id", "u3").exit_code != 0


def test_eval_refuses_a_different_dataset(workspace: Path) -> None:
    args = (
        "eval",
        "--config",
        "a",
        "--split",
        "dev",
        "--trials",
        "1",
        "--limit",
        "1",
        "--run-id",
        "u4",
    )
    assert invoke(*args).exit_code == 0
    assert invoke("data", "--seed", "7", "--out", "data/v1").exit_code == 0
    assert invoke(*args).exit_code != 0


def test_full_test_run_needs_confirmation(workspace: Path) -> None:
    r = invoke(
        "eval", "--config", "a", "--split", "test", "--trials", "1", "--run-id", "u5", input="n\n"
    )
    assert r.exit_code != 0 and not (workspace / "results" / "u5").exists()
