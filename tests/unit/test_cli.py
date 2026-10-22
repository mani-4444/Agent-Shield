from typer.testing import CliRunner

from injbench.cli import app


def test_help_runs() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Agent Shield" in result.output
