"""`injbench` command-line entry point. Subcommands (data, eval, report) arrive in later tasks."""

import typer

app = typer.Typer(name="injbench", no_args_is_help=True)


@app.callback()
def main() -> None:
    """InjectionBench: indirect prompt-injection benchmark for finance agents."""
