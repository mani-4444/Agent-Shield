"""`injbench` command-line entry point."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

if TYPE_CHECKING:
    from injbench.schema import Document, Profile

app = typer.Typer(name="injbench", no_args_is_help=True)


@app.callback()
def main() -> None:
    """InjectionBench: indirect prompt-injection benchmark for finance agents."""


@app.command()
def data(
    seed: Annotated[int, typer.Option(help="Dataset seed.")] = 2026,
    out: Annotated[Path, typer.Option(help="Output directory.")] = Path("data/v1"),
) -> None:
    """Generate profiles, test and dev documents and a manifest (deterministic for a seed)."""
    from injbench.data.generate import build_dataset, write_dataset

    manifest = write_dataset(build_dataset(seed), out, seed)
    typer.echo(f"wrote {out} (dataset_sha256 {manifest['dataset_sha256']})")


@app.command()
def calibrate(
    split: Annotated[str, typer.Option(help="Split to calibrate on (dev only).")] = "dev",
    data_dir: Annotated[Path, typer.Option(help="Dataset directory.")] = Path("data/v1"),
    max_fpr: Annotated[float, typer.Option(help="Allowed benign false-positive rate.")] = 0.05,
) -> None:
    """Print the Prompt Guard threshold for config (c)/(e) from dev benign docs (FPR <= 5%).

    Copy the value into config/models.yaml yourself; that file needs human approval to change.
    """
    from injbench.defenses import default_classifier
    from injbench.defenses.promptguard import calibrate_threshold
    from injbench.schema import Document

    if split != "dev":
        raise typer.BadParameter(
            "calibration uses the dev split only (SPEC.md: never tune on test)"
        )
    lines = (data_dir / "dev.jsonl").read_text(encoding="utf-8").splitlines()
    benign = [d for d in (Document.model_validate_json(x) for x in lines if x) if d.attack is None]
    classifier = default_classifier()
    scores = [classifier(d.ocr_text) for d in benign]
    tau = calibrate_threshold(scores, max_fpr)
    blocked = sum(s >= tau for s in scores)
    typer.echo(f"threshold {tau:.6f}: blocks {blocked}/{len(scores)} dev benign docs")


def _git_sha() -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _load_split(data_dir: Path, split: str) -> tuple[list[Document], dict[str, Profile]]:
    from injbench.schema import Document, Profile

    def lines(name: str) -> list[str]:
        return [x for x in (data_dir / name).read_text(encoding="utf-8").splitlines() if x]

    docs = [Document.model_validate_json(x) for x in lines(f"{split}.jsonl")]
    profiles = [Profile.model_validate_json(x) for x in lines("profiles.jsonl")]
    return docs, {p.profile_id: p for p in profiles}


@app.command("eval")
def eval_(
    config: Annotated[str, typer.Option(help="Configs: comma list of a-e, or 'all'.")],
    run_id: Annotated[str, typer.Option(help="Run name; results go to results/<run_id>.")],
    split: Annotated[str, typer.Option(help="dev or test.")] = "dev",
    trials: Annotated[int, typer.Option(help="Trials per (config, doc).")] = 3,
    limit: Annotated[int | None, typer.Option(help="Only the first N documents.")] = None,
    replay: Annotated[bool, typer.Option(help="Cache only: zero network calls.")] = False,
    data_dir: Annotated[Path, typer.Option(help="Dataset directory.")] = Path("data/v1"),
    results_dir: Annotated[Path, typer.Option(help="Results root.")] = Path("results"),
) -> None:
    """Run configs x docs x trials (resumable): the same --run-id skips finished trials."""
    import json

    from injbench.agent import llm
    from injbench.config import DEFAULT_PATH
    from injbench.defenses import CONFIGS, build_defense, default_settings
    from injbench.runner import run_trials

    if split not in ("dev", "test"):
        raise typer.BadParameter("split must be dev or test")
    configs = list(CONFIGS) if config == "all" else [c.strip() for c in config.split(",") if c]
    unknown = [c for c in configs if c not in CONFIGS]
    if unknown:
        raise typer.BadParameter(f"unknown configs {unknown}; use a-e or all")
    if split == "test" and limit is None and not replay:
        typer.confirm(
            "Full test-split run spends API quota (AGENTS.md: ask first). Continue?", abort=True
        )

    docs, profiles = _load_split(data_dir, split)
    docs = docs[:limit] if limit is not None else docs
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    run_dir = results_dir / run_id
    run_config_path = run_dir / "run_config.json"
    if run_config_path.is_file():
        previous = json.loads(run_config_path.read_text(encoding="utf-8"))
        if previous.get("dataset_sha256") != manifest["dataset_sha256"]:
            raise typer.BadParameter(
                f"{run_dir} was made from a different dataset; use a new --run-id"
            )
    else:
        run_dir.mkdir(parents=True, exist_ok=True)
        run_config = {
            "run_id": run_id, "configs": configs, "split": split, "trials": trials, "limit": limit,
            "data_dir": str(data_dir), "dataset_sha256": manifest["dataset_sha256"],
            "git_sha": _git_sha(), "models_yaml": DEFAULT_PATH.read_text(encoding="utf-8"),
        }  # fmt: skip
        run_config_path.write_text(json.dumps(run_config, indent=2) + "\n", encoding="utf-8")

    llm.configure(cache_dir=Path(".cache/llm"), replay=replay)
    settings = default_settings(git_sha=_git_sha())
    defenses = {c: build_defense(c, settings=settings) for c in configs}
    try:
        records = run_trials(run_dir, defenses, docs, profiles, trials)
    except llm.ReplayMiss as exc:
        typer.echo(f"replay cache miss: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    errors = sum(r.error is not None for r in records)
    typer.echo(f"{run_dir}: {len(records)} records ({errors} with errors)")
