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
