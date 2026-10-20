"""Config (c): Llama Prompt Guard 2 as a pre-filter (DESIGN.md §6, ADR-3).

The classifier scores the agent-visible text (ocr_text) in overlapping token windows and keeps the
maximum malicious probability (Prompt Guard's context is 512 tokens). Score >= threshold -> FLAG
without calling the LLM; otherwise config (a) runs. Scores are cached like LLM responses
(./.cache/promptguard), so replay never loads the model. The threshold is calibrated on dev only.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from injbench.agent.llm import ReplayMiss
from injbench.agent.prompts import plain_user_prompt, policy_text
from injbench.agent.tools import ToolRecorder
from injbench.defenses.base import (
    ClassifierFn,
    LLMFn,
    Settings,
    Trace,
    make_record,
    run_tool_loop,
)
from injbench.schema import Document, Profile, RunRecord

WINDOW = 510  # content tokens per window; + 2 special tokens = 512
STEP = 256
BLOCK_REASON = "prompt_injection_detected"


def windows(ids: Sequence[int], size: int = WINDOW, step: int = STEP) -> list[list[int]]:
    """Overlapping windows covering every token; a short text is one window."""
    if len(ids) <= size:
        return [list(ids)]
    out = [list(ids[i : i + size]) for i in range(0, len(ids) - size + 1, step)]
    if (len(ids) - size) % step:
        out.append(list(ids[-size:]))  # make sure the tail is covered
    return out


class PromptGuard:
    """Local Prompt Guard 2 via transformers (CPU). Loaded lazily on first score."""

    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        self._tok: Any = None
        self._model: Any = None
        self._malicious = 1

    def _load(self) -> None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._tok = AutoTokenizer.from_pretrained(self.model_id)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_id).eval()
        labels = {int(k): str(v).upper() for k, v in self._model.config.id2label.items()}
        hits = [i for i, name in labels.items() if "MALICIOUS" in name or "INJECTION" in name]
        self._malicious = hits[0] if hits else max(labels)

    def __call__(self, text: str) -> float:
        import torch

        if self._model is None:
            self._load()
        ids = self._tok(text, add_special_tokens=False)["input_ids"]
        batch = [self._tok.build_inputs_with_special_tokens(w) for w in windows(ids)]
        width = max(len(b) for b in batch)
        pad = self._tok.pad_token_id or 0
        input_ids = torch.tensor([b + [pad] * (width - len(b)) for b in batch])
        mask = torch.tensor([[1] * len(b) + [0] * (width - len(b)) for b in batch])
        with torch.no_grad():
            logits = self._model(input_ids=input_ids, attention_mask=mask).logits
        return float(torch.softmax(logits, dim=-1)[:, self._malicious].max())


@dataclass
class CachedClassifier:
    """Content-hash cache around a classifier: ./.cache/promptguard/<model>.jsonl."""

    scorer: ClassifierFn
    model_id: str
    cache_dir: Path = Path(".cache/promptguard")
    replay: bool = False
    last_latency_ms: float = 0.0
    _index: dict[str, dict[str, Any]] | None = field(default=None, repr=False)

    def _path(self) -> Path:
        slug = "".join(c if c.isalnum() or c in "-." else "_" for c in self.model_id)
        return self.cache_dir / f"{slug}.jsonl"

    def _key(self, text: str) -> str:
        payload = self.model_id + "\n" + unicodedata.normalize("NFC", text)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load(self) -> dict[str, dict[str, Any]]:
        if self._index is None:
            self._index = {}
            if self._path().is_file():
                for line in self._path().read_text(encoding="utf-8").splitlines():
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    self._index[entry["key"]] = entry
        return self._index

    def __call__(self, text: str) -> float:
        index = self._load()
        key = self._key(text)
        if key in index:
            self.last_latency_ms = float(index[key]["latency_ms"])
            return float(index[key]["score"])
        if self.replay:
            raise ReplayMiss(f"no cached classifier score for {self.model_id} ({key[:12]})")
        start = time.perf_counter()
        score = float(self.scorer(text))
        self.last_latency_ms = (time.perf_counter() - start) * 1000
        entry = {"key": key, "score": score, "latency_ms": self.last_latency_ms}
        self._path().parent.mkdir(parents=True, exist_ok=True)
        with self._path().open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry) + "\n")
        index[key] = entry
        return score


def calibrate_threshold(benign_scores: Sequence[float], max_fpr: float = 0.05) -> float:
    """Smallest threshold whose false-positive rate on benign scores is <= max_fpr (score >= tau
    counts as blocked). Use dev benign docs only, never test."""
    if not benign_scores:
        raise ValueError("need at least one benign score")
    ranked = sorted(benign_scores, reverse=True)
    allowed = math.floor(max_fpr * len(ranked))  # benign docs we may block
    if allowed >= len(ranked):
        return min(ranked)
    cutoff = ranked[allowed]  # the highest score that must stay unblocked
    above = [s for s in ranked if s > cutoff]
    return min(above) if above else math.nextafter(cutoff, math.inf)


@dataclass
class PromptGuardDefense:
    llm: LLMFn
    settings: Settings
    classifier: ClassifierFn
    threshold: float
    name: str = "c"

    def run(self, doc: Document, profile: Profile, trial: int) -> RunRecord:
        started, trace = time.perf_counter(), Trace()
        score, clf_ms = timed_score(self.classifier, doc.ocr_text)
        trace.add_latency("classifier", clf_ms)
        if score >= self.threshold:
            recorder = ToolRecorder()
            recorder.flag_for_review(BLOCK_REASON)
            return make_record(
                self.name, doc, trial, self.settings, trace, started,
                decision="FLAG", tool_calls=recorder.calls, classifier_score=score, blocked=True,
            )  # fmt: skip
        user = plain_user_prompt(doc, profile)
        result = run_tool_loop(self.llm, self.settings, trial, policy_text(), user, trace)
        return make_record(
            self.name, doc, trial, self.settings, trace, started,
            decision=result.decision, tool_calls=result.tool_calls,
            user_message=result.final_text, raw_output=result.raw_output, error=result.error,
            classifier_score=score,
        )  # fmt: skip


def timed_score(classifier: ClassifierFn, text: str) -> tuple[float, float]:
    """Score plus latency; a CachedClassifier reports the originally measured latency."""
    start = time.perf_counter()
    score = float(classifier(text))
    elapsed = (time.perf_counter() - start) * 1000
    return score, getattr(classifier, "last_latency_ms", elapsed) or elapsed
