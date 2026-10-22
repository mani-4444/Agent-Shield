"""Data contracts (DESIGN.md §3). The only types that cross module boundaries.

All models are strict (no type coercion, so "1200" is not an int) and reject unknown fields.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

Decision = Literal["APPROVE", "WAIT", "FLAG", "NO_ACTION"]
DocType = Literal["bank_sms", "receipt_ocr", "chat_message"]
Lang = Literal["en", "te", "te-en"]  # te-en = code-mixed / transliterated
Family = Literal[
    "F1_override", "F2_roleplay", "F3_hidden", "F4_multilingual", "F5_toolarg", "F6_exfil"
]
Goal = Literal["G1_force_approve", "G2_redirect", "G3_exfiltrate"]
Intent = Literal["payment_request", "debit_alert", "receipt"]
Position = Literal["start", "middle", "end", "footer", "hidden"]
Split = Literal["test", "dev"]
ToolName = Literal["approve_payment", "send_message", "flag_for_review"]

VPA_RE = re.compile(r"^[a-z0-9._-]{2,40}@[a-z]{2,20}$")
MAX_AMOUNT_INR = 10_000_000
MAX_MERCHANT_LEN = 60
MAX_DATE_DRIFT_DAYS = 400
CANARY_PREFIX = "CANARY-"


class Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Profile(Model):
    """Trusted user profile. Never sent to the LLM in config (d)."""

    profile_id: str
    monthly_budget_inr: int
    spent_this_month_inr: int
    trusted_payees: list[str]  # VPAs, e.g. "ravi.k@fakepay"
    large_txn_threshold_inr: int
    canary_account_no: str  # "CANARY-4821-7730-15"

    @field_validator("canary_account_no")
    @classmethod
    def _canary_is_fake(cls, v: str) -> str:
        if not v.startswith(CANARY_PREFIX):
            raise ValueError(f"canary must start with {CANARY_PREFIX!r}")
        return v


class GoldFacts(Model):
    intent: Intent
    payee_vpa: str | None
    amount_inr: int  # integer rupees; paise dropped by design
    date: dt.date | None
    merchant: str | None


class ExtractedFacts(GoldFacts):
    """What config (d)/(e)'s LLM must return. Validation is the typed boundary (ADR-1).

    Pass `context={"doc_date": <datetime.date>}` to `model_validate*` to bound `date` to
    ±400 days of the document date.
    """

    @field_validator("payee_vpa")
    @classmethod
    def _vpa_shape(cls, v: str | None) -> str | None:
        if v is not None and not VPA_RE.fullmatch(v):
            raise ValueError("payee_vpa must look like name@handle (lowercase)")
        return v

    @field_validator("amount_inr")
    @classmethod
    def _amount_bounds(cls, v: int) -> int:
        if not 0 <= v <= MAX_AMOUNT_INR:
            raise ValueError(f"amount_inr must be within 0..{MAX_AMOUNT_INR}")
        return v

    @field_validator("merchant")
    @classmethod
    def _merchant_short_single_line(cls, v: str | None) -> str | None:
        if v is not None and (len(v) > MAX_MERCHANT_LEN or "\n" in v or "\r" in v):
            raise ValueError(f"merchant must be one line of at most {MAX_MERCHANT_LEN} chars")
        return v

    @field_validator("date")
    @classmethod
    def _date_near_doc(cls, v: dt.date | None, info: ValidationInfo) -> dt.date | None:
        doc_date: dt.date | None = (info.context or {}).get("doc_date")
        if (
            v is not None
            and doc_date is not None
            and abs((v - doc_date).days) > MAX_DATE_DRIFT_DAYS
        ):
            raise ValueError(f"date must be within {MAX_DATE_DRIFT_DAYS} days of the document")
        return v


class AttackMeta(Model):
    family: Family
    goal: Goal
    payload: str
    position: Position
    payload_lang: Lang
    attacker_vpa: str | None
    attacker_amount_inr: int | None
    attacker_contact: str | None


class Document(Model):
    doc_id: str
    split: Split
    doc_type: DocType
    lang: Lang
    profile_id: str
    visible_text: str  # what a human sees
    ocr_text: str  # what the agent sees (== visible_text unless F3)
    gold: GoldFacts
    gold_decision: Decision
    twin_id: str | None  # set on poisoned docs
    attack: AttackMeta | None


class ToolCall(Model):
    name: ToolName
    args: dict[str, str | int]


def record_key(config: str, doc_id: str, trial: int) -> str:
    return f"{config}|{doc_id}|{trial}"


class RunRecord(Model):
    """One trial: one config on one document. One JSONL line in records.jsonl."""

    key: str  # record_key(config, doc_id, trial)
    config: str
    doc_id: str
    trial: int
    model_id: str
    git_sha: str
    decision: Decision
    tool_calls: list[ToolCall]
    user_message: str
    raw_output: str
    extracted: ExtractedFacts | None
    classifier_score: float | None
    blocked_by_classifier: bool
    latency_ms: dict[str, float]  # {"classifier": …, "llm": …, "engine": …, "total": …}
    tokens: dict[str, int]
    error: str | None
    cache_hit: bool

    @model_validator(mode="after")
    def _key_matches(self) -> RunRecord:
        if self.key != record_key(self.config, self.doc_id, self.trial):
            raise ValueError("key must be 'config|doc_id|trial'")
        return self


class ToolSpec(Model):
    """A tool offered to the LLM (configs a-c only): name, description, JSON-schema parameters."""

    name: ToolName
    description: str
    parameters: dict[str, Any]


class Message(Model):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)  # assistant turns that called tools
    tool_call_id: str | None = None  # tool-result turns


class LLMRequest(Model):
    """Everything sent to the provider. Its JSON form is the cache key input (agent/llm.py)."""

    provider: str
    model_id: str
    messages: list[Message]
    tools: list[ToolSpec] = Field(default_factory=list)
    response_schema: dict[str, Any] | None = None  # JSON schema for structured output (config d)
    temperature: float
    max_tokens: int | None
    reasoning_effort: str | None = None  # e.g. "none" turns off qwen3 thinking on Ollama
    trial: int  # part of the cache key so the 3 trials are distinct, replayable calls


class LLMResponse(Model):
    text: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tokens: dict[str, int] = Field(default_factory=dict)
    latency_ms: float = 0.0  # provider latency; on a cache hit, the latency recorded originally
    cache_hit: bool = False


class MetricValue(Model):
    """One metric cell: point estimate, 95% cluster-bootstrap CI, documents behind it."""

    value: float | None
    lo: float | None
    hi: float | None
    n_docs: int


class SummaryRow(Model):
    config: str
    group: str  # "all", or "family=<F>", "goal=<G>", "lang=<L>"
    metrics: dict[str, MetricValue]


class LabelCheck(Model):
    """Detector-human agreement on hand-labelled trials (R10)."""

    agreement: float
    n: int
    disagreements: list[str]


class WebConfigRow(Model):
    """One config's metrics for the showcase site (copied from summary.csv)."""

    config: str
    name: str  # plain-language name, e.g. "Strict fact-checker"
    what: str  # one-sentence description for non-technical readers
    group: str  # "all" or "family=<F>" / "goal=<G>" / "lang=<L>"
    metrics: dict[str, MetricValue]


class WebRun(Model):
    run_id: str
    model_ids: list[str]
    n_docs: int
    trials: int
    n_records: int
    threshold: float | None
    run_date: str | None
    rows: list[WebConfigRow]


class WebAction(Model):
    text: str  # what the assistant did, in everyday words
    attack_succeeded: bool


class WebExample(Model):
    doc_id: str
    family: str
    family_name: str
    goal: str
    goal_name: str
    lang: Lang
    message: str  # what the agent read (OCR layer)
    hidden_from_humans: bool  # F3: the payload is not visible to a person
    hidden_instruction: str
    correct: str  # the right action, in everyday words
    actions: dict[str, WebAction]  # config -> what it did (trial 0)


class ModelSpec(Model):
    provider: str
    model_id: str
    reasoning_effort: str | None = None


class ClassifierSpec(Model):
    model_id: str | None
    threshold: float | None


class ModelsConfig(Model):
    """config/models.yaml. Values still marked TODO load as None."""

    primary: ModelSpec
    secondary: ModelSpec
    payload_drafter: ModelSpec
    classifier: ClassifierSpec
    temperature: float
    max_tokens: int | None
    trials: int
    data_seed: int
    bootstrap_seed: int
