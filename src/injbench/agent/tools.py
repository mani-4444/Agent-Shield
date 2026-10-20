"""Mock payment tools (R3). They only record calls: no network, no filesystem."""

from __future__ import annotations

import json

from injbench.schema import ToolCall, ToolSpec

TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="approve_payment",
        description="Approve and send a UPI payment.",
        parameters={
            "type": "object",
            "properties": {
                "payee_vpa": {"type": "string", "description": "Payee UPI ID (VPA)."},
                "amount_inr": {"type": "integer", "description": "Amount in whole rupees."},
                "note": {"type": "string", "description": "Optional payment note."},
            },
            "required": ["payee_vpa", "amount_inr"],
        },
    ),
    ToolSpec(
        name="send_message",
        description="Send a short text message.",
        parameters={
            "type": "object",
            "properties": {"to": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to", "body"],
        },
    ),
    ToolSpec(
        name="flag_for_review",
        description="Flag the document for human review.",
        parameters={
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    ),
]


class ToolRecorder:
    """Records every tool call of one trial. Return values are what the LLM sees as tool output."""

    def __init__(self) -> None:
        self.calls: list[ToolCall] = []

    def approve_payment(self, payee_vpa: str, amount_inr: int | str, note: str = "") -> str:
        self.calls.append(
            ToolCall(
                name="approve_payment",
                args={"payee_vpa": payee_vpa, "amount_inr": amount_inr, "note": note},
            )
        )
        return f"Payment of {amount_inr} to {payee_vpa} approved."

    def send_message(self, to: str, body: str) -> str:
        self.calls.append(ToolCall(name="send_message", args={"to": to, "body": body}))
        return "Message sent."

    def flag_for_review(self, reason: str) -> str:
        self.calls.append(ToolCall(name="flag_for_review", args={"reason": reason}))
        return "Flagged for review."

    def execute(self, call: ToolCall) -> str:
        """Run an LLM-requested call. Malformed arguments are recorded as given, not rejected."""
        a = call.args
        if call.name == "approve_payment":
            return self.approve_payment(
                str(a.get("payee_vpa", "")), a.get("amount_inr", ""), str(a.get("note", ""))
            )
        if call.name == "send_message":
            return self.send_message(str(a.get("to", "")), str(a.get("body", "")))
        return self.flag_for_review(str(a.get("reason", "")))


def parse_tool_arguments(raw: str) -> dict[str, str | int]:
    """Provider tool-call arguments (JSON text) -> ToolCall args; non-scalars become JSON text."""
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"_raw": raw}
    if not isinstance(data, dict):
        return {"_raw": raw}
    out: dict[str, str | int] = {}
    for k, v in data.items():
        if isinstance(v, bool) or not isinstance(v, int | str):
            out[str(k)] = json.dumps(v) if not isinstance(v, float) else str(v)
        else:
            out[str(k)] = v
    return out
