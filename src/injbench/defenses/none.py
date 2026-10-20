"""Config (a): no defense. The baseline every other config is compared with."""

from __future__ import annotations

import time
from dataclasses import dataclass

from injbench.agent.prompts import plain_user_prompt, policy_text
from injbench.defenses.base import LLMFn, Settings, Trace, make_record, run_tool_loop
from injbench.schema import Document, Profile, RunRecord


@dataclass
class NoDefense:
    llm: LLMFn
    settings: Settings
    name: str = "a"

    def run(self, doc: Document, profile: Profile, trial: int) -> RunRecord:
        started, trace = time.perf_counter(), Trace()
        user = plain_user_prompt(doc, profile)
        result = run_tool_loop(self.llm, self.settings, trial, policy_text(), user, trace)
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
