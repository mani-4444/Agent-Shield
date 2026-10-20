"""Seeded randomness. Every random choice in the project goes through make_rng (AGENTS.md).

The stream depends only on (seed, *keys), never on call order, process or platform, so any
single document can be regenerated alone: make_rng(2026, "attack", doc_id).
"""

from __future__ import annotations

import hashlib
import json
import unicodedata

import numpy as np


def make_rng(seed: int, *keys: str | int) -> np.random.Generator:
    """Independent generator for (seed, *keys). String keys are NFC-normalised first."""
    parts: list[str | int] = [seed]
    for k in keys:
        if isinstance(k, bool) or not isinstance(k, str | int):
            raise TypeError(f"rng keys must be str or int, got {type(k).__name__}")
        parts.append(unicodedata.normalize("NFC", k) if isinstance(k, str) else k)
    digest = hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode("utf-8")).digest()
    return np.random.Generator(np.random.PCG64(int.from_bytes(digest, "big")))
