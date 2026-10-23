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
    """Agent Shield: indirect prompt-injection benchmark for finance agents."""


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
    threshold: Annotated[
        float | None, typer.Option(help="Override the classifier threshold for (c)/(e).")
    ] = None,
    model: Annotated[
        str, typer.Option(help="Model role from models.yaml: primary or secondary.")
    ] = "primary",
    retry_errors: Annotated[
        bool, typer.Option(help="Re-run trials that failed with a provider error.")
    ] = False,
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
            "run_id": run_id,
            "configs": configs,
            "split": split,
            "trials": trials,
            "limit": limit,
            "data_dir": str(data_dir),
            "dataset_sha256": manifest["dataset_sha256"],
            "git_sha": _git_sha(),
            "models_yaml": DEFAULT_PATH.read_text(encoding="utf-8"),
            "threshold_override": threshold,
            "model_role": model,
        }
        run_config_path.write_text(json.dumps(run_config, indent=2) + "\n", encoding="utf-8")

    llm.configure(cache_dir=Path(".cache/llm"), replay=replay)
    settings = default_settings(git_sha=_git_sha(), role=model)
    defenses = {c: build_defense(c, settings=settings, threshold=threshold) for c in configs}
    try:
        records = run_trials(run_dir, defenses, docs, profiles, trials, retry_errors=retry_errors)
    except llm.ReplayMiss as exc:
        typer.echo(f"replay cache miss: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    errors = sum(r.error is not None for r in records)
    typer.echo(f"{run_dir}: {len(records)} records ({errors} with errors)")


@app.command()
def report(
    run: Annotated[Path, typer.Option(help="Run directory, e.g. results/<run_id>.")],
) -> None:
    """Write summary.md, summary.csv, pareto.png, heatmap.png and gallery.md for a run."""
    from injbench.config import DEFAULT_PATH, load_models_config
    from injbench.report import write_report

    seed = load_models_config(DEFAULT_PATH).bootstrap_seed if DEFAULT_PATH.is_file() else 2026
    for path in write_report(run, seed=seed):
        typer.echo(f"wrote {path}")


@app.command("label-sample")
def label_sample(
    run: Annotated[Path, typer.Option(help="Run directory.")],
    n: Annotated[int, typer.Option(help="Trials to label.")] = 60,
    seed: Annotated[
        int | None, typer.Option(help="Sampling seed (default: bootstrap_seed in models.yaml).")
    ] = None,
    exclude: Annotated[
        list[Path] | None, typer.Option(help="Earlier sheet(s) whose trials must not be drawn.")
    ] = None,
    out: Annotated[
        Path | None, typer.Option(help="Sheet path (default <run>/label_sheet.csv).")
    ] = None,
) -> None:
    """Write a sheet of n poisoned trials (stratified by config x goal) to label. Never
    overwrites an existing sheet, so filled labels cannot be lost."""
    from injbench.config import DEFAULT_PATH, load_models_config
    from injbench.labelcheck import sample_for_labelling, sheet_keys, write_sheet
    from injbench.report import load_run

    path = out or run / "label_sheet.csv"
    if path.exists():
        typer.echo(f"{path} already exists; choose another --out", err=True)
        raise typer.Exit(1)
    records, docs, _ = load_run(run)
    if seed is None:
        seed = load_models_config(DEFAULT_PATH).bootstrap_seed if DEFAULT_PATH.is_file() else 2026
    skip = set().union(*(sheet_keys(p) for p in exclude or []))
    sample = sample_for_labelling(records, docs, n=n, seed=seed, exclude=skip)
    write_sheet(path, sample, docs)
    typer.echo(f"wrote {path} ({len(sample)} trials, seed {seed}): fill human_attack_success")


@app.command("label-score")
def label_score(
    run: Annotated[Path, typer.Option(help="Run directory.")],
    labels: Annotated[
        Path | None, typer.Option(help="Filled sheet (default <run>/label_sheet.csv).")
    ] = None,
    out: Annotated[
        Path | None, typer.Option(help="Report path (default <run>/label_check.md).")
    ] = None,
) -> None:
    """Compare hand labels with attack_success and write a label-check report."""
    from injbench.labelcheck import agreement_report, read_sheet, write_label_check
    from injbench.report import load_run

    records, docs, profiles = load_run(run)
    result = agreement_report(
        records, docs, profiles, read_sheet(labels or run / "label_sheet.csv")
    )
    report = out or run / "label_check.md"
    write_label_check(report, result)
    typer.echo(f"agreement {result.agreement * 100:.1f}% on {result.n} trials -> {report}")


@app.command("export-web")
def export_web_cmd(
    run: Annotated[Path, typer.Option(help="Main run directory.")] = Path("results/v1-main"),
    out: Annotated[Path, typer.Option(help="Output directory.")] = Path("web/src/data"),
    secondary: Annotated[Path | None, typer.Option(help="Secondary-model run.")] = Path(
        "results/v1-secondary"
    ),
    tau05: Annotated[Path | None, typer.Option(help="Threshold-0.5 run.")] = Path(
        "results/v1-main-t05"
    ),
    run_date: Annotated[str | None, typer.Option(help="Run date shown on the site.")] = None,
) -> None:
    """Export a finished run as JSON for the showcase site (numbers copied from summary.csv)."""
    from injbench.webexport import export_web

    def present(p: Path | None) -> Path | None:
        return p if p is not None and (p / "summary.csv").is_file() else None

    for path in export_web(
        run, out, secondary_dir=present(secondary), tau05_dir=present(tau05), run_date=run_date
    ):
        typer.echo(f"wrote {path}")
