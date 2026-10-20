"""The five defense configs behind one interface (R4): build_defense(c).run(doc, profile, trial)."""

from __future__ import annotations

from pathlib import Path

from injbench.config import DEFAULT_PATH, load_models_config
from injbench.defenses.base import ClassifierFn, Defense, LLMFn, Settings

CONFIGS = ("a", "b", "c", "d", "e")


def default_settings(path: Path = DEFAULT_PATH, git_sha: str = "unknown") -> Settings:
    cfg = load_models_config(path)
    return Settings(
        model=cfg.primary,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        seed=cfg.data_seed,
        git_sha=git_sha,
    )


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
    from injbench.defenses.spotlight import Spotlight

    settings = settings or default_settings()
    llm_fn: LLMFn = llm or adapter.complete
    if config == "a":
        return NoDefense(llm_fn, settings)
    if config == "b":
        return Spotlight(llm_fn, settings)
    raise ValueError(f"unknown or not yet implemented config {config!r}; expected one of {CONFIGS}")
