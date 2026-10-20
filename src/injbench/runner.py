"""Resumable runner (R6, DESIGN.md §8): configs x docs x trials -> results/<run_id>/records.jsonl.

One JSONL line per trial, appended and flushed before the next trial starts. On restart, finished
keys are skipped; a half-written or duplicate line left by a killed run is dropped first.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from pydantic import ValidationError

from injbench.defenses.base import Defense
from injbench.schema import Document, Profile, RunRecord, record_key

RECORDS = "records.jsonl"
PROGRESS = "progress.log"


def load_records(path: Path) -> list[RunRecord]:
    """Valid records in file order (first occurrence per key); bad or partial lines are skipped."""
    if not path.is_file():
        return []
    seen: set[str] = set()
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = RunRecord.model_validate_json(line)
        except ValidationError:
            continue
        if record.key not in seen:
            seen.add(record.key)
            records.append(record)
    return records


def repair(path: Path) -> list[RunRecord]:
    """Rewrite records.jsonl with only valid, unique lines if anything else is in it."""
    records = load_records(path)
    if path.is_file():
        clean = "".join(r.model_dump_json() + "\n" for r in records)
        if path.read_text(encoding="utf-8") != clean:
            path.write_text(clean, encoding="utf-8", newline="\n")
    return records


def run_trials(
    run_dir: Path,
    defenses: Mapping[str, Defense],
    docs: Sequence[Document],
    profiles: Mapping[str, Profile],
    trials: int,
    on_progress: Callable[[int, int, RunRecord], None] | None = None,
) -> list[RunRecord]:
    """Run every missing (config, doc, trial) and return all records of the run."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / RECORDS
    done = {r.key for r in repair(path)}
    total = len(defenses) * len(docs) * trials
    hits = 0
    with (
        path.open("a", encoding="utf-8", newline="\n") as out,
        (run_dir / PROGRESS).open("a", encoding="utf-8", newline="\n") as log,
    ):
        for config, defense in defenses.items():
            for doc in docs:
                for trial in range(trials):
                    key = record_key(config, doc.doc_id, trial)
                    if key in done:
                        continue
                    record = defense.run(doc, profiles[doc.profile_id], trial)
                    if record.key != key:
                        raise ValueError(
                            f"defense {config!r} returned key {record.key!r} for {key!r}"
                        )
                    out.write(record.model_dump_json() + "\n")
                    out.flush()
                    done.add(key)
                    hits += int(record.cache_hit)
                    stamp = time.strftime("%H:%M:%S")
                    log.write(f"{stamp} {len(done)}/{total} {key} cache_hits={hits}\n")
                    log.flush()
                    if on_progress:
                        on_progress(len(done), total, record)
    return load_records(path)
