"""Config (d): typed LLM/deterministic boundary (ADR-1).

The LLM gets only the document text and the ExtractedFacts JSON schema: no profile, no canary, no
tools. Its output is validated; one retry carries the validation error; a second failure is
FLAG("schema_invalid"). engine.decide then makes the decision and tool calls from the validated
facts, and user_message comes from the engine's fixed template.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from injbench.agent.engine import decide, user_message
from injbench.agent.llm import ReplayMiss
from injbench.agent.prompts import EXTRACTION_SYSTEM, extraction_user_prompt, retry_prompt
from injbench.agent.tools import ToolRecorder
from injbench.defenses.base import LLMFn, Settings, Trace, error_text, make_record
from injbench.schema import Document, ExtractedFacts, LLMRequest, Message, Profile, RunRecord

SCHEMA_INVALID = "schema_invalid"


def strip_fences(text: str) -> str:
    """Accept a bare JSON object or one wrapped in a ``` / ```json fence; nothing else."""
    t = text.strip()
    if t.startswith("```"):
        t = t[3:]
        if t[:4].lower() == "json":
            t = t[4:]
        t = t.rsplit("```", 1)[0] if t.rstrip().endswith("```") else t
    return t.strip()


def extract(
    llm: LLMFn, settings: Settings, doc: Document, trial: int, trace: Trace
) -> tuple[ExtractedFacts | None, str, str | None]:
    """(facts or None, raw outputs, validation error of the last attempt)."""
    messages = [
        Message(role="system", content=EXTRACTION_SYSTEM),
        Message(role="user", content=extraction_user_prompt(doc)),
    ]
    raw: list[str] = []
    error: str | None = None
    for _attempt in range(2):
        request = LLMRequest(
            provider=settings.model.provider,
            model_id=settings.model.model_id,
            messages=messages,
            response_schema=ExtractedFacts.model_json_schema(),
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            trial=trial,
        )
        response = trace.call(llm, request)
        raw.append(response.text)
        try:
            return (
                ExtractedFacts.model_validate_json(strip_fences(response.text)),
                "\n".join(raw),
                None,
            )
        except ValidationError as exc:
            error = str(exc)[:1000]
            messages = [
                *messages,
                Message(role="assistant", content=response.text),
                Message(role="user", content=retry_prompt(error)),
            ]
    return None, "\n".join(raw), error


def boundary_outcome(
    llm: LLMFn, settings: Settings, doc: Document, profile: Profile, trial: int, trace: Trace
) -> dict[str, Any]:
    """Keyword arguments for make_record: shared by configs (d) and (e)."""
    try:
        facts, raw, _ = extract(llm, settings, doc, trial, trace)
    except ReplayMiss:
        raise
    except Exception as exc:
        return {"decision": "FLAG", "tool_calls": [], "error": error_text(exc)}
    if facts is None:
        recorder = ToolRecorder()
        recorder.flag_for_review(SCHEMA_INVALID)
        return {"decision": "FLAG", "tool_calls": recorder.calls, "raw_output": raw}
    start = time.perf_counter()
    decision, tools = decide(facts, profile)
    trace.add_latency("engine", (time.perf_counter() - start) * 1000)
    return {
        "decision": decision,
        "tool_calls": tools,
        "user_message": user_message(decision, facts),
        "raw_output": raw,
        "extracted": facts,
    }


@dataclass
class BoundaryDefense:
    llm: LLMFn
    settings: Settings
    name: str = "d"

    def run(self, doc: Document, profile: Profile, trial: int) -> RunRecord:
        started, trace = time.perf_counter(), Trace()
        outcome = boundary_outcome(self.llm, self.settings, doc, profile, trial, trace)
        return make_record(self.name, doc, trial, self.settings, trace, started, **outcome)
