"""Load config/models.yaml, the only home of model IDs, sampling settings and seeds (AGENTS.md)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]  # stubs would be a new dependency

from injbench.schema import ClassifierSpec, ModelsConfig, ModelSpec

DEFAULT_PATH = Path("config/models.yaml")


def _todo_to_none(value: Any) -> Any:
    return None if isinstance(value, str) and value.upper().startswith("TODO") else value


def _model(raw: dict[str, Any]) -> ModelSpec:
    effort = _todo_to_none(raw.get("reasoning_effort"))
    return ModelSpec(
        provider=str(raw["provider"]),
        model_id=str(raw["model_id"]),
        reasoning_effort=None if effort is None else str(effort),
    )


def load_models_config(path: Path = DEFAULT_PATH) -> ModelsConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    models, sampling, seeds = raw["models"], raw["sampling"], raw["seeds"]
    clf = models["classifier"]
    threshold = _todo_to_none(clf.get("threshold"))
    max_tokens = _todo_to_none(sampling.get("max_tokens"))
    return ModelsConfig(
        primary=_model(models["primary"]),
        secondary=_model(models["secondary"]),
        payload_drafter=_model(models["payload_drafter"]),
        classifier=ClassifierSpec(
            model_id=_todo_to_none(clf.get("model_id")),
            threshold=None if threshold is None else float(threshold),
        ),
        temperature=float(sampling["temperature"]),
        max_tokens=None if max_tokens is None else int(max_tokens),
        trials=int(sampling["trials"]),
        data_seed=int(seeds["data"]),
        bootstrap_seed=int(seeds["bootstrap"]),
    )


def is_pinned(spec: ModelSpec) -> bool:
    return not (
        spec.provider.upper().startswith("TODO") or spec.model_id.upper().startswith("TODO")
    )
