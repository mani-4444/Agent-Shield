"""Config (b): spotlighting (Hines et al. 2024): a per-trial random boundary token plus
datamarking, and a system line saying marked text is data, never instructions."""

from __future__ import annotations

import time
from dataclasses import dataclass

from injbench.agent.prompts import spotlight_system, spotlight_user_prompt
from injbench.defenses.base import LLMFn, Settings, Trace, make_record, run_tool_loop
from injbench.rng import make_rng
from injbench.schema import Document, Profile, RunRecord


def boundary_token(seed: int, doc_id: str, trial: int) -> str:
    raw = make_rng(seed, "spotlight", doc_id, trial).integers(0, 256, size=4)
    return "".join(f"{int(b):02x}" for b in raw)


@dataclass
class Spotlight:
    llm: LLMFn
    settings: Settings
    name: str = "b"

    def run(self, doc: Document, profile: Profile, trial: int) -> RunRecord:
        started, trace = time.perf_counter(), Trace()
        token = boundary_token(self.settings.seed, doc.doc_id, trial)
        system = spotlight_system(token)
        user = spotlight_user_prompt(doc, profile, token)
        result = run_tool_loop(self.llm, self.settings, trial, system, user, trace)
        return make_record(
            self.name,
            doc,
            trial,
            self.settings,
            trace,
            started,
            decision=result.decision,
            tool_calls=result.tool_calls,
            user_message=result.final_text,
            raw_output=result.raw_output,
            error=result.error,
        )
