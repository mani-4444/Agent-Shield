from pathlib import Path
from typing import Any

import pytest

from injbench.agent import llm
from injbench.schema import LLMRequest, LLMResponse, Message


def request(text: str = "hello", trial: int = 0, model: str = "m1") -> LLMRequest:
    return LLMRequest(
        provider="groq",
        model_id=model,
        messages=[Message(role="user", content=text)],
        temperature=0.0,
        max_tokens=None,
        trial=trial,
    )


class FakeTransport:
    def __init__(self, fail_with: list[Exception] | None = None) -> None:
        self.calls = 0
        self.fail_with = list(fail_with or [])

    def __call__(self, req: LLMRequest) -> LLMResponse:
        self.calls += 1
        if self.fail_with:
            raise self.fail_with.pop(0)
        return LLMResponse(
            text=f"echo {req.messages[-1].content}", tokens={"prompt": 3}, latency_ms=42.0
        )


class StatusError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(status_code)
        self.status_code = status_code


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeTransport:
    fake = FakeTransport()
    monkeypatch.setattr(llm, "transport", fake)
    monkeypatch.setattr(llm, "sleep", lambda s: None)
    llm.configure(cache_dir=tmp_path / "llm", replay=False)
    return fake


def test_second_identical_call_is_a_cache_hit(isolated: FakeTransport) -> None:
    first = llm.complete(request())
    second = llm.complete(request())
    assert isolated.calls == 1
    assert (first.cache_hit, second.cache_hit) == (False, True)
    assert (
        second.text == first.text and second.latency_ms == 42.0 and second.tokens == {"prompt": 3}
    )


def test_trial_is_part_of_the_key(isolated: FakeTransport) -> None:
    llm.complete(request(trial=0))
    llm.complete(request(trial=1))
    assert isolated.calls == 2


def test_nfc_equivalent_requests_share_a_cache_entry(isolated: FakeTransport) -> None:
    import unicodedata

    llm.complete(request("తెలుగు"))
    llm.complete(request(unicodedata.normalize("NFD", "తెలుగు")))
    assert isolated.calls == 1


def test_cache_survives_a_fresh_process(tmp_path: Path, isolated: FakeTransport) -> None:
    llm.complete(request())
    llm.configure(cache_dir=tmp_path / "llm")  # drops the in-memory index, reloads from disk
    assert llm.complete(request()).cache_hit
    assert isolated.calls == 1
    assert len(list((tmp_path / "llm").glob("*.jsonl"))) == 1


def test_half_written_cache_line_is_ignored(tmp_path: Path, isolated: FakeTransport) -> None:
    llm.complete(request())
    path = next((tmp_path / "llm").glob("*.jsonl"))
    with path.open("a", encoding="utf-8") as f:
        f.write('{"key": "abc", "resp')
    llm.configure(cache_dir=tmp_path / "llm")
    assert llm.complete(request()).cache_hit


def test_replay_hit_and_miss(isolated: FakeTransport) -> None:
    llm.complete(request("cached"))
    llm.configure(replay=True)
    try:
        assert llm.complete(request("cached")).cache_hit
        with pytest.raises(llm.ReplayMiss):
            llm.complete(request("never seen"))
        assert isolated.calls == 1
    finally:
        llm.configure(replay=False)


@pytest.mark.parametrize("status", [429, 500, 503])
def test_retries_transient_errors(
    isolated: FakeTransport, status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    waits: list[float] = []
    monkeypatch.setattr(llm, "sleep", waits.append)
    isolated.fail_with = [StatusError(status), StatusError(status)]
    assert llm.complete(request()).text == "echo hello"
    assert isolated.calls == 3 and len(waits) == 2 and waits[1] > waits[0] - 1


def test_gives_up_after_max_retries(isolated: FakeTransport) -> None:
    isolated.fail_with = [StatusError(429)] * (llm.MAX_RETRIES + 1)
    with pytest.raises(StatusError):
        llm.complete(request())
    assert isolated.calls == llm.MAX_RETRIES + 1


def test_non_retryable_error_fails_fast(isolated: FakeTransport) -> None:
    isolated.fail_with = [StatusError(400)]
    with pytest.raises(StatusError):
        llm.complete(request())
    assert isolated.calls == 1


def test_failed_calls_are_not_cached(isolated: FakeTransport) -> None:
    isolated.fail_with = [StatusError(400)]
    with pytest.raises(StatusError):
        llm.complete(request())
    assert llm.complete(request()).text == "echo hello"


def test_real_transport_refuses_unpinned_models() -> None:
    with pytest.raises(llm.NotPinned):
        llm.openai_transport(request(model="TODO-pin-at-T08"))


def test_openai_message_mapping_keeps_tool_round_trip() -> None:
    from injbench.schema import ToolCall

    req = LLMRequest(
        provider="groq",
        model_id="m",
        temperature=0.0,
        max_tokens=None,
        trial=0,
        messages=[
            Message(
                role="assistant",
                content="",
                tool_calls=[ToolCall(name="flag_for_review", args={"reason": "x"})],
            ),
            Message(role="tool", content="Flagged.", tool_call_id="call_0"),
        ],
    )
    out: list[dict[str, Any]] = llm.to_openai_messages(req)
    assert out[0]["tool_calls"][0]["id"] == "call_0"
    assert out[0]["tool_calls"][0]["function"] == {
        "name": "flag_for_review",
        "arguments": '{"reason": "x"}',
    }
    assert out[1]["tool_call_id"] == "call_0"
