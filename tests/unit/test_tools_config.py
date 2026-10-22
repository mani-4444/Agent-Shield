from pathlib import Path

from injbench.agent.tools import TOOL_SPECS, ToolRecorder, parse_tool_arguments
from injbench.config import is_pinned, load_models_config
from injbench.schema import ModelSpec, ToolCall

ROOT = Path(__file__).resolve().parents[2]


def test_tool_specs_cover_the_three_tools() -> None:
    assert [t.name for t in TOOL_SPECS] == ["approve_payment", "send_message", "flag_for_review"]


def test_execute_records_llm_calls_verbatim() -> None:
    rec = ToolRecorder()
    rec.execute(
        ToolCall(name="approve_payment", args={"payee_vpa": "a@fakepay", "amount_inr": "1,200"})
    )
    rec.execute(ToolCall(name="send_message", args={"to": "user", "body": "hi"}))
    assert rec.calls[0].args == {"payee_vpa": "a@fakepay", "amount_inr": "1,200", "note": ""}
    assert [c.name for c in rec.calls] == ["approve_payment", "send_message"]


def test_parse_tool_arguments_handles_odd_shapes() -> None:
    assert parse_tool_arguments('{"amount_inr": 1200, "note": "x"}') == {
        "amount_inr": 1200,
        "note": "x",
    }
    assert parse_tool_arguments('{"amount_inr": 1200.5}') == {"amount_inr": "1200.5"}
    assert parse_tool_arguments('{"tags": ["a"]}') == {"tags": '["a"]'}
    assert parse_tool_arguments("not json") == {"_raw": "not json"}
    assert parse_tool_arguments("") == {}


def test_models_yaml_loads_with_todo_as_none() -> None:
    cfg = load_models_config(ROOT / "config" / "models.yaml")
    assert cfg.temperature == 0.0 and cfg.trials == 3 and cfg.data_seed == 2026
    assert cfg.bootstrap_seed == 2026
    assert cfg.classifier.threshold == 0.001122  # calibrated on dev at T10 (approved)


def test_is_pinned() -> None:
    assert not is_pinned(ModelSpec(provider="TODO", model_id="TODO-pin-at-T08"))
    assert is_pinned(ModelSpec(provider="groq", model_id="some-model"))


def test_reasoning_effort_is_optional_and_loaded(tmp_path: Path) -> None:
    import yaml  # type: ignore[import-untyped]

    def write(**primary_extra: str) -> Path:
        cfg = {
            "models": {
                "primary": {"provider": "ollama", "model_id": "m", **primary_extra},
                "secondary": {"provider": "groq", "model_id": "s"},
                "payload_drafter": {"provider": "anthropic", "model_id": "c"},
                "classifier": {"model_id": "TODO", "threshold": "TODO"},
            },
            "sampling": {"temperature": 0, "max_tokens": 1024, "trials": 3},
            "seeds": {"data": 2026, "bootstrap": 2026},
        }
        path = tmp_path / "models.yaml"
        path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        return path

    assert load_models_config(write()).primary.reasoning_effort is None
    assert load_models_config(write(reasoning_effort="none")).primary.reasoning_effort == "none"
    assert load_models_config(write()).max_tokens == 1024


def test_pinned_config_uses_local_qwen_without_thinking() -> None:
    cfg = load_models_config(ROOT / "config" / "models.yaml")
    assert is_pinned(cfg.primary) and cfg.primary.reasoning_effort == "none"
