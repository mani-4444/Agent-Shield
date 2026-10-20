"""`injbench` command-line entry point."""

from pathlib import Path
from typing import Annotated

import typer

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
