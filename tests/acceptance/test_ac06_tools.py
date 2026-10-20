"""AC-6 (R3): every tool call is logged in the trial record; tools never open a network
connection (sockets fully disabled here, loopback included) and never touch the filesystem.
"""

from __future__ import annotations

import builtins
from pathlib import Path

import pytest
from acceptance_support import FakeLLM, facts_json, make_doc, make_profile, reply


@pytest.mark.disable_socket
def test_tool_recorder_logs_every_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from injbench.agent.tools import ToolRecorder

    monkeypatch.chdir(tmp_path)

    def no_open(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"tool touched the filesystem: open{args}")

    rec = ToolRecorder()
    monkeypatch.setattr(builtins, "open", no_open)
    rec.approve_payment(payee_vpa="ravi.k@fakepay", amount_inr=1200, note="rent")
    rec.send_message(to="user", body="Approved Rs 1200 to ravi.k@fakepay")
    rec.flag_for_review(reason="unknown payee")
    monkeypatch.undo()

    assert [c.name for c in rec.calls] == ["approve_payment", "send_message", "flag_for_review"]
    assert rec.calls[0].args["payee_vpa"] == "ravi.k@fakepay"
    assert rec.calls[0].args["amount_inr"] == 1200
    assert rec.calls[1].args["to"] == "user"
    assert rec.calls[2].args["reason"] == "unknown payee"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.disable_socket
def test_config_a_llm_tool_calls_land_in_record() -> None:
    from injbench.defenses import build_defense

    args: dict[str, str | int] = {"payee_vpa": "ravi.k@fakepay", "amount_inr": 1200, "note": "rent"}
    llm = FakeLLM(
        [reply(tool_calls=[("approve_payment", args)]), reply("Paid.\nDECISION: APPROVE")]
    )
    record = build_defense("a", llm=llm).run(make_doc("doc-a-1"), make_profile(), 0)

    assert record.decision == "APPROVE"
    paid = [c for c in record.tool_calls if c.name == "approve_payment"]
    assert len(paid) == 1
    assert paid[0].args["payee_vpa"] == "ravi.k@fakepay"
    assert paid[0].args["amount_inr"] == 1200


@pytest.mark.disable_socket
def test_config_d_engine_tool_calls_land_in_record() -> None:
    from injbench.defenses import build_defense

    llm = FakeLLM([reply(facts_json(payee_vpa="ravi.k@fakepay", amount_inr=1200))])
    record = build_defense("d", llm=llm).run(make_doc("doc-d-1"), make_profile(), 0)

    assert record.decision == "APPROVE"
    assert [(c.name, c.args["payee_vpa"], c.args["amount_inr"]) for c in record.tool_calls] == [
        ("approve_payment", "ravi.k@fakepay", 1200)
    ]
