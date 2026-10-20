"""AC-13 (R8): `report` writes summary.md, summary.csv, pareto.png, heatmap.png and gallery.md with
>=3 examples per config.

Format contract: summary.csv has a `config` column holding the config letter; gallery.md has one
"## Config <x>" section per config (letter optionally in brackets); each example is a "### "
heading.
The run uses a fake provider that always answers "DECISION: NO_ACTION", so (a)/(b) mostly decide
NO_ACTION and (d) ends in FLAG(schema_invalid): plenty of failures on the dev split.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import pytest
from acceptance_support import REPORT_FILES, reply, run_cli

pytestmark = pytest.mark.disable_socket
CONFIGS = ("a", "b", "d")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def report_dir(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from injbench.agent import llm

    def transport(request: Any) -> Any:
        return reply("DECISION: NO_ACTION")

    monkeypatch.setattr(llm, "transport", transport)
    run_cli(
        [
            "eval",
            "--config",
            ",".join(CONFIGS),
            "--split",
            "dev",
            "--trials",
            "1",
            "--run-id",
            "rep",
        ]
    )
    run_cli(["report", "--run", "results/rep"])
    return workspace / "results" / "rep"


def test_report_writes_all_outputs(report_dir: Path) -> None:
    missing = [f for f in REPORT_FILES if not (report_dir / f).is_file()]
    assert not missing
    for png in ("pareto.png", "heatmap.png"):
        assert (report_dir / png).read_bytes()[:8] == PNG_MAGIC, f"{png} is not a PNG"
    assert (report_dir / "summary.md").read_text(encoding="utf-8").strip()


def test_summary_csv_has_every_config(report_dir: Path) -> None:
    with (report_dir / "summary.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows and "config" in rows[0]
    assert set(CONFIGS) <= {r["config"] for r in rows}


def test_gallery_has_three_examples_per_config(report_dir: Path) -> None:
    counts: dict[str, int] = {}
    current = None
    for line in (report_dir / "gallery.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## Config \(?([a-e])\)?", line)
        if m:
            current = m.group(1)
            counts.setdefault(current, 0)
        elif line.startswith("### ") and current:
            counts[current] += 1
    short = {c: counts.get(c, 0) for c in CONFIGS if counts.get(c, 0) < 3}
    assert not short, f"gallery examples per config: {counts}"
