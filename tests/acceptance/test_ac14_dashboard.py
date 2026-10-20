"""AC-14 (R9): the Streamlit dashboard starts without error in replay mode (AppTest smoke test).

Replay is the dashboard's default (DESIGN.md §10). It must cope with no results at all, and must
load a real run from ./results when one exists. Tabs: Results, Explorer, Live demo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from acceptance_support import REPO_ROOT, reply, run_cli

DASHBOARD = REPO_ROOT / "app" / "dashboard.py"
TABS = {"Results", "Explorer", "Live demo"}


def _start() -> Any:
    from streamlit.testing.v1 import AppTest

    assert DASHBOARD.is_file(), f"missing {DASHBOARD}"
    at = AppTest.from_file(str(DASHBOARD), default_timeout=120)
    at.run()
    assert not at.exception, [e.message for e in at.exception]
    return at


def test_dashboard_starts_with_no_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    at = _start()
    assert {t.label for t in at.tabs} >= TABS


def test_dashboard_loads_a_run(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from injbench.agent import llm

    monkeypatch.setattr(llm, "transport", lambda request: reply("DECISION: NO_ACTION"))
    run_cli(
        [
            "eval",
            "--config",
            "a,d",
            "--split",
            "dev",
            "--trials",
            "1",
            "--limit",
            "5",
            "--run-id",
            "dash",
        ]
    )
    run_cli(["report", "--run", "results/dash"])
    at = _start()
    assert {t.label for t in at.tabs} >= TABS
