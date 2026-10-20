"""Session fixtures: one generated dataset shared by AC-2..AC-5, AC-11, AC-13, AC-14."""

from __future__ import annotations

from pathlib import Path

import pytest
from acceptance_support import Dataset, generate_dataset, make_workspace


@pytest.fixture(scope="session")
def dataset_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return generate_dataset(tmp_path_factory.mktemp("gen") / "v1")


@pytest.fixture(scope="session")
def dataset(dataset_dir: Path) -> Dataset:
    return Dataset(dataset_dir)


@pytest.fixture
def workspace(tmp_path: Path, dataset_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """cwd = a fresh project dir with config/ and data/v1/; results/ and .cache/ land here."""
    root = make_workspace(tmp_path, dataset_dir)
    monkeypatch.chdir(root)
    return root
