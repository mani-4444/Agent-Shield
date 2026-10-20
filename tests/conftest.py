"""Shared pytest setup.

Network is blocked by default via pytest-socket (`--allow-hosts=127.0.0.1,::1` in pyproject.toml):
any connection to a non-loopback host raises. Tests marked `live` (deselected unless `-m live`)
get real sockets back.
"""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if item.get_closest_marker("live"):
            item.add_marker(pytest.mark.enable_socket)
