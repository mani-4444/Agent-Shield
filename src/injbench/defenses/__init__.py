"""The five defense configs behind one interface (R4): build_defense(c).run(doc, profile, trial)."""

from __future__ import annotations

from pathlib import Path

from injbench.config import DEFAULT_PATH, load_models_config
from injbench.defenses.base import ClassifierFn, Defense, LLMFn, Settings

CONFIGS = ("a", "b", "c", "d", "e")


class NotCalibrated(RuntimeError):
    """Config (c)/(e) needs a classifier threshold and model ID in config/models.yaml (T10)."""


def default_settings(path: Path = DEFAULT_PATH, git_sha: str = "unknown") -> Settings:
    cfg = load_models_config(path)
    return Settings(
        model=cfg.primary,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        seed=cfg.data_seed,
        git_sha=git_sha,
    )


def default_classifier(path: Path = DEFAULT_PATH) -> ClassifierFn:
    """Cached local Prompt Guard 2; replay follows the LLM adapter's replay flag."""
    from injbench.agent import llm as adapter
    from injbench.defenses.promptguard import CachedClassifier, PromptGuard

    model_id = load_models_config(path).classifier.model_id
    if model_id is None:
        raise NotCalibrated("set models.classifier.model_id in config/models.yaml (T10)")
    return CachedClassifier(PromptGuard(model_id), model_id, replay=adapter.replay_enabled())


def default_threshold(path: Path = DEFAULT_PATH) -> float:
    threshold = load_models_config(path).classifier.threshold
    if threshold is None:
        raise NotCalibrated("calibrate the threshold on dev and set it in config/models.yaml (T10)")
    return threshold


def build_defense(
    config: str,
    *,
    llm: LLMFn | None = None,
    classifier: ClassifierFn | None = None,
    threshold: float | None = None,
    settings: Settings | None = None,
) -> Defense:
    """Construct config (a)-(e). Defaults: the cached adapter and config/models.yaml settings."""
    from injbench.agent import llm as adapter
    from injbench.defenses.none import NoDefense
    from injbench.defenses.promptguard import PromptGuardDefense
    from injbench.defenses.spotlight import Spotlight

    settings = settings or default_settings()
    llm_fn: LLMFn = llm or adapter.complete
    if config == "a":
        return NoDefense(llm_fn, settings)
    if config == "b":
        return Spotlight(llm_fn, settings)
    if config == "c":
        tau = default_threshold() if threshold is None else threshold
        return PromptGuardDefense(llm_fn, settings, classifier or default_classifier(), tau)
    raise ValueError(f"unknown or not yet implemented config {config!r}; expected one of {CONFIGS}")
