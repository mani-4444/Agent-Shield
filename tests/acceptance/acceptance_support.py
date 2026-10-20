"""Shared helpers for the acceptance suite (protected after T02).

Production imports happen inside functions so that a missing module makes a test *fail*
(ImportError) instead of breaking collection for the whole suite.
"""

from __future__ import annotations

import json
import shutil
import unicodedata
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from injbench.schema import Document, LLMRequest, LLMResponse, Profile, RunRecord

ACCEPTANCE_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = ACCEPTANCE_DIR / "fixtures" / "detectors"
REPO_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), Path.cwd()
)

DATA_FILES = ("profiles.jsonl", "test.jsonl", "dev.jsonl", "manifest.json")
REPORT_FILES = ("summary.md", "summary.csv", "pareto.png", "heatmap.png", "gallery.md")
FAMILIES = ("F1_override", "F2_roleplay", "F3_hidden", "F4_multilingual", "F5_toolarg", "F6_exfil")
GOALS = ("G1_force_approve", "G2_redirect", "G3_exfiltrate")
DECISIONS = ("APPROVE", "WAIT", "FLAG", "NO_ACTION")
TOOL_NAMES = ("approve_payment", "send_message", "flag_for_review")


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def run_cli(args: Sequence[str], *, expect_ok: bool = True) -> Any:
    """Invoke the `injbench` Typer app in-process and return the Click result."""
    from typer.testing import CliRunner

    from injbench.cli import app

    result = CliRunner().invoke(app, list(args))
    if expect_ok:
        assert result.exit_code == 0, (
            f"`injbench {' '.join(args)}` exited {result.exit_code}\n{result.output}\n"
            f"{result.exception!r}"
        )
    return result


def read_jsonl(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class Dataset:
    """A generated dataset directory loaded through the schema models."""

    def __init__(self, root: Path) -> None:
        from injbench.schema import Document, Profile

        self.root = root
        self.profiles: dict[str, Profile] = {}
        for line in read_jsonl(root / "profiles.jsonl"):
            p = Profile.model_validate_json(line)
            self.profiles[p.profile_id] = p
        self.test: list[Document] = [
            Document.model_validate_json(x) for x in read_jsonl(root / "test.jsonl")
        ]
        self.dev: list[Document] = [
            Document.model_validate_json(x) for x in read_jsonl(root / "dev.jsonl")
        ]

    @property
    def docs(self) -> list[Document]:
        return self.test + self.dev

    def by_id(self) -> dict[str, Document]:
        return {d.doc_id: d for d in self.docs}


def generate_dataset(out: Path, seed: int = 2026) -> Path:
    run_cli(["data", "--seed", str(seed), "--out", str(out)])
    return out


def make_workspace(tmp_path: Path, dataset_dir: Path) -> Path:
    """A throwaway project dir: config/ from the repo and data/v1/ from a generated dataset."""
    shutil.copytree(REPO_ROOT / "config", tmp_path / "config")
    shutil.copytree(dataset_dir, tmp_path / "data" / "v1")
    return tmp_path


# --- builders for hand-made objects -------------------------------------------------------------

CANARY = "CANARY-4821-7730-15"


def make_profile(**overrides: Any) -> Profile:
    from injbench.schema import Profile

    fields: dict[str, Any] = {
        "profile_id": "prof-test-01",
        "monthly_budget_inr": 20000,
        "spent_this_month_inr": 5000,
        "trusted_payees": ["ravi.k@fakepay", "meena.store@examplebank"],
        "large_txn_threshold_inr": 10000,
        "canary_account_no": CANARY,
    }
    fields.update(overrides)
    return Profile(**fields)


def make_doc(
    doc_id: str,
    *,
    intent: str = "payment_request",
    payee_vpa: str | None = "ravi.k@fakepay",
    amount_inr: int = 1200,
    gold_decision: str = "APPROVE",
    text: str | None = None,
    profile_id: str = "prof-test-01",
    split: str = "dev",
    attack: dict[str, Any] | None = None,
    twin_id: str | None = None,
) -> Document:
    from injbench.schema import AttackMeta, Document, GoldFacts

    body = text or f"Please pay Rs {amount_inr} to {payee_vpa or 'the merchant'}. Thanks."
    return Document(
        doc_id=doc_id,
        split=split,
        doc_type="chat_message" if intent == "payment_request" else "bank_sms",
        lang="en",
        profile_id=profile_id,
        visible_text=body,
        ocr_text=body,
        gold=GoldFacts(
            intent=intent,
            payee_vpa=payee_vpa,
            amount_inr=amount_inr,
            date=None if intent != "debit_alert" else date(2026, 10, 1),
            merchant=None,
        ),
        gold_decision=gold_decision,
        twin_id=twin_id,
        attack=AttackMeta(**attack) if attack else None,
    )


def make_record(
    config: str,
    doc_id: str,
    trial: int,
    *,
    decision: str = "NO_ACTION",
    tool_calls: Sequence[tuple[str, dict[str, str | int]]] = (),
    user_message: str = "",
    blocked: bool = False,
    total_ms: float = 100.0,
    tokens: dict[str, int] | None = None,
) -> RunRecord:
    from injbench.schema import RunRecord, ToolCall

    return RunRecord(
        key=f"{config}|{doc_id}|{trial}",
        config=config,
        doc_id=doc_id,
        trial=trial,
        model_id="fake-model",
        git_sha="0000000",
        decision=decision,
        tool_calls=[ToolCall(name=n, args=a) for n, a in tool_calls],
        user_message=user_message,
        raw_output="",
        extracted=None,
        classifier_score=0.99 if blocked else None,
        blocked_by_classifier=blocked,
        latency_ms={"total": total_ms},
        tokens={"prompt": 100, "completion": 20} if tokens is None else tokens,
        error=None,
        cache_hit=False,
    )


# --- fake LLM -------------------------------------------------------------------------------------


class FakeLLM:
    """Stands in for the LLM callable a defense receives; records every request."""

    def __init__(self, replies: Sequence[LLMResponse] | Callable[[int], LLMResponse]) -> None:
        self._replies = replies
        self.requests: list[LLMRequest] = []

    def __call__(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        n = len(self.requests) - 1
        if callable(self._replies):
            return self._replies(n)
        return self._replies[min(n, len(self._replies) - 1)]

    @property
    def calls(self) -> int:
        return len(self.requests)

    def sent_text(self) -> str:
        """Everything sent to the provider, as one string (the request's JSON form)."""
        return "\n".join(r.model_dump_json() for r in self.requests)


def reply(text: str = "", tool_calls: Sequence[tuple[str, dict[str, str | int]]] = ()) -> Any:
    from injbench.schema import LLMResponse, ToolCall

    return LLMResponse(
        text=text,
        tool_calls=[ToolCall(name=n, args=a) for n, a in tool_calls],
        tokens={"prompt": 50, "completion": 10},
    )


def facts_json(**overrides: Any) -> str:
    fields: dict[str, Any] = {
        "intent": "payment_request",
        "payee_vpa": "ravi.k@fakepay",
        "amount_inr": 1200,
        "date": None,
        "merchant": None,
    }
    fields.update(overrides)
    return json.dumps(fields)


def load_fixtures() -> list[dict[str, Any]]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(FIXTURES_DIR.glob("*.json"))]
