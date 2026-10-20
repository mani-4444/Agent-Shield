"""AC-11 (R6, R12): `eval --replay` then `report` on a completed run make zero network calls and
regenerate summary.csv byte-identical. Replay also serves a fresh run entirely from the cache, and
raises (non-zero exit) on a cache miss instead of calling out (DESIGN.md §7).

LLM seam: injbench.agent.llm.complete() caches around the module attribute `transport`
(LLMRequest -> LLMResponse), which is the only code that talks to a provider. Tests replace it.
The cache lives under ./.cache and runs under ./results (cwd = the workspace fixture).
Sockets are fully disabled in this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from acceptance_support import read_jsonl, reply, run_cli

pytestmark = pytest.mark.disable_socket

EVAL = ["eval", "--config", "a,d", "--split", "dev", "--trials", "1", "--limit", "5"]


class Transport:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls = 0

    def __call__(self, request: Any) -> Any:
        self.calls += 1
        if not self.allowed:
            raise AssertionError("replay must not reach the provider")
        return reply("DECISION: NO_ACTION")


def _use(monkeypatch: pytest.MonkeyPatch, transport: Transport) -> Transport:
    from injbench.agent import llm

    monkeypatch.setattr(llm, "transport", transport)
    return transport


def _outcomes(run: Path) -> set[tuple[str, str, str, str]]:
    from injbench.schema import RunRecord

    recs = [RunRecord.model_validate_json(x) for x in read_jsonl(run / "records.jsonl")]
    return {(r.key, r.decision, r.raw_output, repr(r.tool_calls)) for r in recs}


def test_replay_and_report_are_byte_identical(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live = _use(monkeypatch, Transport())
    run_cli([*EVAL, "--run-id", "r1"])
    run_cli(["report", "--run", "results/r1"])
    assert live.calls > 0
    summary = workspace / "results" / "r1" / "summary.csv"
    first = summary.read_bytes()
    assert len(read_jsonl(workspace / "results" / "r1" / "records.jsonl")) == 2 * 5

    summary.unlink()
    blocked = _use(monkeypatch, Transport(allowed=False))
    run_cli([*EVAL, "--run-id", "r1", "--replay"])
    run_cli(["report", "--run", "results/r1"])
    assert blocked.calls == 0
    assert summary.read_bytes() == first


def test_replay_serves_fresh_run_from_cache(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(monkeypatch, Transport())
    run_cli([*EVAL, "--run-id", "live"])

    blocked = _use(monkeypatch, Transport(allowed=False))
    run_cli([*EVAL, "--run-id", "replayed", "--replay"])
    assert blocked.calls == 0
    assert _outcomes(workspace / "results" / "replayed") == _outcomes(
        workspace / "results" / "live"
    )


def test_replay_cache_miss_fails_without_calling_out(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    blocked = _use(monkeypatch, Transport(allowed=False))
    result = run_cli([*EVAL, "--run-id", "miss", "--replay"], expect_ok=False)
    assert result.exit_code != 0
    assert blocked.calls == 0
