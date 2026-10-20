"""Config (e): config (c)'s classifier gate in front of config (d)'s typed boundary."""

from __future__ import annotations

import time
from dataclasses import dataclass

from injbench.agent.tools import ToolRecorder
from injbench.defenses.base import ClassifierFn, LLMFn, Settings, Trace, make_record
from injbench.defenses.boundary import boundary_outcome
from injbench.defenses.promptguard import BLOCK_REASON, timed_score
from injbench.schema import Document, Profile, RunRecord


@dataclass
class CombinedDefense:
    llm: LLMFn
    settings: Settings
    classifier: ClassifierFn
    threshold: float
    name: str = "e"

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
        outcome = boundary_outcome(self.llm, self.settings, doc, profile, trial, trace)
        return make_record(
            self.name, doc, trial, self.settings, trace, started, classifier_score=score, **outcome
        )
