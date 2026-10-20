"""The only path to an LLM provider (AGENTS.md): cache, replay, retries, latency.

`complete(request)` looks the request up in a content-hash cache (./.cache/llm/*.jsonl by default),
otherwise calls the module attribute `transport` with backoff on 429/5xx. With replay on, a cache
miss raises ReplayMiss and nothing is sent. Tests replace `transport`; nothing else may call a
provider SDK.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from injbench.schema import LLMRequest, LLMResponse, ToolCall

MAX_RETRIES = 6
PROVIDERS: dict[str, tuple[str, str]] = {  # name -> (OpenAI-compatible base URL, API key env var)
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY"),
    "ollama": ("http://localhost:11434/v1", ""),
}
TOOL_NAMES = ("approve_payment", "send_message", "flag_for_review")


class ReplayMiss(LookupError):
    """--replay was requested and this request is not in the cache."""


class NotPinned(RuntimeError):
    """config/models.yaml still has a TODO model; refuse to call out."""


@dataclass
class _State:
    cache_dir: Path = Path(".cache/llm")
    replay: bool = False
    index: dict[str, dict[str, Any]] = field(default_factory=dict)
    loaded: bool = False


_state = _State()
sleep: Callable[[float], None] = time.sleep


def configure(*, cache_dir: Path | None = None, replay: bool | None = None) -> None:
    """Set cache location and replay mode (the CLI calls this once per run)."""
    if cache_dir is not None:
        _state.cache_dir, _state.index, _state.loaded = cache_dir, {}, False
    if replay is not None:
        _state.replay = replay


def replay_enabled() -> bool:
    return _state.replay


def cache_key(request: LLMRequest) -> str:
    text = unicodedata.normalize("NFC", request.model_dump_json())
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cache_file(request: LLMRequest) -> Path:
    name = f"{request.provider}_{request.model_id}"
    slug = "".join(c if c.isalnum() or c in "-." else "_" for c in name)
    return _state.cache_dir / f"{slug}.jsonl"


def _load() -> None:
    if _state.loaded:
        return
    if _state.cache_dir.is_dir():
        for path in sorted(_state.cache_dir.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a half-written line from a killed run
                _state.index[entry["key"]] = entry
    _state.loaded = True


def _store(request: LLMRequest, key: str, response: LLMResponse) -> None:
    entry = {
        "key": key,
        "response": response.model_dump(mode="json", exclude={"cache_hit"}),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = _cache_file(request)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()
    _state.index[key] = entry


def _retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status == 429 or status >= 500
    return type(exc).__name__ in {"APIConnectionError", "APITimeoutError", "RateLimitError"}


def _call_with_backoff(request: LLMRequest) -> LLMResponse:
    attempt = 0
    while True:
        try:
            return transport(request)
        except Exception as exc:
            if attempt >= MAX_RETRIES or not _retryable(exc):
                raise
            sleep(min(60.0, 2.0**attempt) + random.uniform(0, 1))  # jitter, not crypto
            attempt += 1


def complete(request: LLMRequest) -> LLMResponse:
    """Cached LLM call. Raises ReplayMiss on a miss in replay mode; provider errors propagate."""
    _load()
    key = cache_key(request)
    hit = _state.index.get(key)
    if hit is not None:
        return LLMResponse.model_validate({**hit["response"], "cache_hit": True})
    if _state.replay:
        raise ReplayMiss(
            f"no cached response for {request.provider}/{request.model_id} ({key[:12]})"
        )
    start = time.perf_counter()
    response = _call_with_backoff(request)
    elapsed = (time.perf_counter() - start) * 1000
    response = response.model_copy(
        update={"latency_ms": response.latency_ms or elapsed, "cache_hit": False}
    )
    _store(request, key, response)
    return response


# --- real provider transport ----------------------------------------------------------------------


def to_openai_messages(request: LLMRequest) -> list[dict[str, Any]]:
    """Schema messages -> OpenAI chat format. Tool-call ids are positional ("call_<k>")."""
    out: list[dict[str, Any]] = []
    for m in request.messages:
        msg: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": f"call_{k}",
                    "type": "function",
                    "function": {"name": c.name, "arguments": json.dumps(c.args)},
                }
                for k, c in enumerate(m.tool_calls)
            ]
        if m.tool_call_id is not None:
            msg["tool_call_id"] = m.tool_call_id
        out.append(msg)
    return out


def openai_transport(request: LLMRequest) -> LLMResponse:
    """Call an OpenAI-compatible endpoint (Groq, Gemini compatibility API, Ollama)."""
    from injbench.agent.tools import parse_tool_arguments

    if request.provider.upper().startswith("TODO") or request.model_id.upper().startswith("TODO"):
        raise NotPinned("pin provider and model_id in config/models.yaml before live calls (T08)")
    if request.provider not in PROVIDERS:
        raise ValueError(
            f"unknown provider {request.provider!r}; expected one of {sorted(PROVIDERS)}"
        )

    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    base_url, key_env = PROVIDERS[request.provider]
    api_key = os.environ.get(key_env, "") if key_env else "ollama"
    client = OpenAI(base_url=base_url, api_key=api_key, max_retries=0)
    kwargs: dict[str, Any] = {
        "model": request.model_id,
        "messages": to_openai_messages(request),
        "temperature": request.temperature,
    }
    if request.max_tokens is not None:
        kwargs["max_tokens"] = request.max_tokens
    if request.tools:
        kwargs["tools"] = [
            {"type": "function", "function": t.model_dump(mode="json")} for t in request.tools
        ]
    if request.response_schema is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "extracted_facts", "schema": request.response_schema},
        }
    start = time.perf_counter()
    resp = client.chat.completions.create(**kwargs)
    latency = (time.perf_counter() - start) * 1000
    message = resp.choices[0].message
    calls = []
    for c in message.tool_calls or []:
        fn = getattr(c, "function", None)
        if fn is not None and fn.name in TOOL_NAMES:
            calls.append(ToolCall(name=fn.name, args=parse_tool_arguments(fn.arguments)))
    usage = resp.usage
    tokens = {"prompt": usage.prompt_tokens, "completion": usage.completion_tokens} if usage else {}
    return LLMResponse(
        text=message.content or "", tool_calls=calls, tokens=tokens, latency_ms=latency
    )


transport: Callable[[LLMRequest], LLMResponse] = openai_transport
