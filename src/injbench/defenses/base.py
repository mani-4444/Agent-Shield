"""Shared machinery for the five configs (DESIGN.md §6): the Defense interface, the tool loop
used by (a)-(c), decision parsing and record assembly."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, cast

from injbench.agent.llm import ReplayMiss
from injbench.agent.tools import TOOL_SPECS, ToolRecorder
from injbench.schema import (
    Decision,
    Document,
    ExtractedFacts,
    LLMRequest,
    LLMResponse,
    Message,
    ModelSpec,
    Profile,
    RunRecord,
    ToolCall,
    record_key,
)

LLMFn = Callable[[LLMRequest], LLMResponse]
ClassifierFn = Callable[[str], float]
MAX_TOOL_ROUNDS = 3
DECISION_RE = re.compile(r"DECISION:\s*(APPROVE|WAIT|FLAG|NO_ACTION)\b", re.IGNORECASE)


class Defense(Protocol):
    name: str

    def run(self, doc: Document, profile: Profile, trial: int) -> RunRecord: ...


@dataclass(frozen=True)
class Settings:
    model: ModelSpec
    temperature: float
    max_tokens: int | None
    seed: int
    git_sha: str = "unknown"


@dataclass
class Trace:
    """Per-trial accounting across LLM calls and stages."""

    latency_ms: dict[str, float] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=dict)
    llm_calls: int = 0
    cache_hits: int = 0

    def add_latency(self, stage: str, ms: float) -> None:
        self.latency_ms[stage] = self.latency_ms.get(stage, 0.0) + ms

    def call(self, llm: LLMFn, request: LLMRequest) -> LLMResponse:
        response = llm(request)
        self.llm_calls += 1
        self.cache_hits += int(response.cache_hit)
        self.add_latency("llm", response.latency_ms)
        for k, v in response.tokens.items():
            self.tokens[k] = self.tokens.get(k, 0) + v
        return response


def parse_decision(text: str) -> Decision | None:
    """The last `DECISION: X` in the text, if any."""
    matches = DECISION_RE.findall(text)
    return cast(Decision, matches[-1].upper()) if matches else None


def make_record(
    config: str,
    doc: Document,
    trial: int,
    settings: Settings,
    trace: Trace,
    started: float,
    *,
    decision: Decision,
    tool_calls: list[ToolCall],
    user_message: str = "",
    raw_output: str = "",
    extracted: ExtractedFacts | None = None,
    classifier_score: float | None = None,
    blocked: bool = False,
    error: str | None = None,
) -> RunRecord:
    latency = dict(trace.latency_ms)
    latency["total"] = (time.perf_counter() - started) * 1000
    return RunRecord(
        key=record_key(config, doc.doc_id, trial),
        config=config,
        doc_id=doc.doc_id,
        trial=trial,
        model_id=settings.model.model_id,
        git_sha=settings.git_sha,
        decision=decision,
        tool_calls=tool_calls,
        user_message=user_message,
        raw_output=raw_output,
        extracted=extracted,
        classifier_score=classifier_score,
        blocked_by_classifier=blocked,
        latency_ms=latency,
        tokens=dict(trace.tokens),
        error=error,
        cache_hit=trace.llm_calls > 0 and trace.cache_hits == trace.llm_calls,
    )


def error_text(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:500]


@dataclass
class ToolLoopResult:
    decision: Decision
    tool_calls: list[ToolCall]
    final_text: str
    raw_output: str
    error: str | None


def run_tool_loop(
    llm: LLMFn, settings: Settings, trial: int, system: str, user: str, trace: Trace
) -> ToolLoopResult:
    """Configs (a)-(c): the LLM sees policy + profile + document and may call the mock tools for
    up to MAX_TOOL_ROUNDS rounds. A missing DECISION line or a provider error ends in FLAG with
    `error` set. ReplayMiss propagates so `--replay` fails loudly."""
    messages = [Message(role="system", content=system), Message(role="user", content=user)]
    recorder = ToolRecorder()
    texts: list[str] = []
    decision: Decision | None = None
    try:
        for round_no in range(MAX_TOOL_ROUNDS + 1):
            request = LLMRequest(
                provider=settings.model.provider,
                model_id=settings.model.model_id,
                messages=messages,
                tools=TOOL_SPECS,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                reasoning_effort=settings.model.reasoning_effort,
                trial=trial,
            )
            response = trace.call(llm, request)
            texts.append(response.text)
            decision = parse_decision(response.text)
            if not response.tool_calls or round_no == MAX_TOOL_ROUNDS:
                break
            results = [recorder.execute(call) for call in response.tool_calls]
            if decision is not None:  # tools and a final decision in the same turn
                break
            messages = [
                *messages,
                Message(role="assistant", content=response.text, tool_calls=response.tool_calls),
                *(
                    Message(role="tool", content=result, tool_call_id=f"call_{k}")
                    for k, result in enumerate(results)
                ),
            ]
    except ReplayMiss:
        raise
    except Exception as exc:
        return ToolLoopResult("FLAG", recorder.calls, "", "\n".join(texts), error_text(exc))
    final = texts[-1] if texts else ""
    if decision is None:
        return ToolLoopResult("FLAG", recorder.calls, final, "\n".join(texts), "no_decision")
    return ToolLoopResult(decision, recorder.calls, final, "\n".join(texts), None)
