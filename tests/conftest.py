"""Shared pytest setup.

Network is blocked by default via pytest-socket (`--allow-hosts=127.0.0.1,::1` in pyproject.toml):
any connection to a non-loopback host raises. Tests marked `live` (deselected unless `-m live`)
get real sockets back.

Acceptance tests (tests/acceptance/, protected) are written before the code (T02). Until a task
implements its AC, its tests are listed in PENDING_ACCEPTANCE and run as strict xfail: the suite
stays green, and a pending test that starts passing fails as XPASS, so the task that makes it
pass must delete its entry here.
See the raw failures with `uv run pytest tests/acceptance --runxfail`.
"""

import pytest

# "file" or "file::test" (without parametrize ids) -> task that turns it green (PLAN.md).
PENDING_ACCEPTANCE = {
    "test_ac10_resume.py": "T12",
    "test_ac11_replay.py": "T12",
    "test_ac12_metrics.py": "T13",
    "test_ac13_report.py": "T17",
    "test_ac14_dashboard.py": "T19",
    "test_ac15_labelcheck.py": "T18",
}

# Pending tests that would pass vacuously before their task lands, so they are not run at all.
# test_replay_cache_miss expects a non-zero exit; a missing `eval` command (exit 2) satisfies it.
NOT_RUN_UNTIL_IMPLEMENTED = {
    "test_ac11_replay.py::test_replay_cache_miss_fails_without_calling_out",
}


def _pending_task(item: pytest.Item) -> str | None:
    if item.path.parent.name != "acceptance":
        return None
    name = getattr(item, "originalname", item.name)
    return PENDING_ACCEPTANCE.get(f"{item.path.name}::{name}") or PENDING_ACCEPTANCE.get(
        item.path.name
    )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if item.get_closest_marker("live"):
            item.add_marker(pytest.mark.enable_socket)
        task = _pending_task(item)
        if task:
            run = f"{item.path.name}::{getattr(item, 'originalname', item.name)}" not in (
                NOT_RUN_UNTIL_IMPLEMENTED
            )
            item.add_marker(
                pytest.mark.xfail(strict=True, run=run, reason=f"pending: implemented in {task}")
            )
