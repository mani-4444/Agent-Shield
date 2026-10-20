"""AC-1 (R1): `injbench data --seed 2026 --out DIR` twice -> identical bytes, same manifest hash."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from acceptance_support import DATA_FILES, generate_dataset


def test_generation_is_byte_identical(tmp_path: Path) -> None:
    a = generate_dataset(tmp_path / "a" / "v1")
    b = generate_dataset(tmp_path / "b" / "v1")

    names_a = sorted(p.name for p in a.iterdir())
    names_b = sorted(p.name for p in b.iterdir())
    assert names_a == names_b
    assert set(DATA_FILES) <= set(names_a), f"missing outputs: {set(DATA_FILES) - set(names_a)}"
    for name in names_a:
        assert (a / name).read_bytes() == (b / name).read_bytes(), f"{name} differs between runs"

    ma = json.loads((a / "manifest.json").read_text(encoding="utf-8"))
    mb = json.loads((b / "manifest.json").read_text(encoding="utf-8"))
    assert ma["dataset_sha256"] == mb["dataset_sha256"]


def test_manifest_hashes_match_files(dataset_dir: Path) -> None:
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    files: dict[str, str] = manifest["files"]
    assert set(files) == set(DATA_FILES) - {"manifest.json"}
    for name, digest in files.items():
        assert hashlib.sha256((dataset_dir / name).read_bytes()).hexdigest() == digest, name
    assert len(manifest["dataset_sha256"]) == 64


def test_different_seed_changes_dataset(tmp_path: Path, dataset_dir: Path) -> None:
    other = generate_dataset(tmp_path / "other" / "v1", seed=7)
    a = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    b = json.loads((other / "manifest.json").read_text(encoding="utf-8"))
    assert a["dataset_sha256"] != b["dataset_sha256"]
