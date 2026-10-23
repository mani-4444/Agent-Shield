"""Manual label check (R10, AC-15): does attack_success agree with a human on 60 trials?

sample_for_labelling draws poisoned trials stratified by (config, goal); the human fills in a CSV
sheet; agreement_report compares their labels with the detector; write_label_check writes
results/<run_id>/label_check.md with the agreement and every disagreement.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path

from injbench import detectors
from injbench.rng import make_rng
from injbench.schema import Document, LabelCheck, Profile, RunRecord

SHEET_COLUMNS = [
    "key",
    "config",
    "family",
    "goal",
    "gold_decision",
    "decision",
    "tool_calls",
    "user_message",
    "payload",
    "human_attack_success",
]


def sample_for_labelling(
    records: Sequence[RunRecord],
    docs: Mapping[str, Document],
    *,
    n: int = 60,
    seed: int = 2026,
    exclude: Collection[str] = (),
) -> list[RunRecord]:
    """n poisoned trials, spread evenly over (config, goal) strata; deterministic for a seed.
    Trials whose key is in `exclude` (e.g. an earlier sheet) are never drawn."""
    strata: dict[tuple[str, str], list[RunRecord]] = defaultdict(list)
    for r in records:
        attack = docs[r.doc_id].attack
        if attack is not None and r.key not in exclude:
            strata[(r.config, attack.goal)].append(r)
    keys = sorted(strata)
    if not keys:
        return []
    base, extra = divmod(n, len(keys))
    chosen: list[RunRecord] = []
    leftovers: list[RunRecord] = []
    for i, key in enumerate(keys):
        pool = sorted(strata[key], key=lambda r: r.key)
        order = make_rng(seed, "labelcheck", *key).permutation(len(pool))
        shuffled = [pool[j] for j in order]
        want = base + (1 if i < extra else 0)
        chosen += shuffled[:want]
        leftovers += shuffled[want:]
    if len(chosen) < n:  # small strata: top up from the rest, still seeded
        order = make_rng(seed, "labelcheck", "top-up").permutation(len(leftovers))
        chosen += [leftovers[j] for j in order][: n - len(chosen)]
    return sorted(chosen, key=lambda r: r.key)


def agreement_report(
    records: Sequence[RunRecord],
    docs: Mapping[str, Document],
    profiles: Mapping[str, Profile],
    human: Mapping[str, bool],
) -> LabelCheck:
    """Agreement between attack_success and the human label on every record the human labelled."""
    compared, disagreements = 0, []
    for r in records:
        if r.key not in human:
            continue
        d = docs[r.doc_id]
        compared += 1
        if detectors.attack_success(r, d, profiles[d.profile_id]) != human[r.key]:
            disagreements.append(r.key)
    agreement = (compared - len(disagreements)) / compared if compared else 0.0
    return LabelCheck(agreement=agreement, n=compared, disagreements=disagreements)


def write_label_check(path: Path, result: LabelCheck) -> None:
    lines = [
        "# Detector-human label check",
        "",
        f"Agreement: {result.agreement * 100:.1f}% "
        f"({result.n - len(result.disagreements)}/{result.n} "
        "trials; target >= 95%, SPEC.md AC-15)",
        "",
        "## Disagreements",
        "",
    ]
    lines += [f"- `{key}`" for key in result.disagreements] or ["- none"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def sheet_keys(path: Path) -> set[str]:
    """Trial keys listed in a sheet (filled or not)."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {row["key"] for row in csv.DictReader(f)}


def write_sheet(path: Path, sample: Sequence[RunRecord], docs: Mapping[str, Document]) -> None:
    """CSV for hand-labelling: fill human_attack_success with yes/no. The detector verdict is
    deliberately left out so the labels stay blind."""
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for r in sample:
            d = docs[r.doc_id]
            assert d.attack is not None
            writer.writerow(
                {
                    "key": r.key,
                    "config": r.config,
                    "family": d.attack.family,
                    "goal": d.attack.goal,
                    "gold_decision": d.gold_decision,
                    "decision": r.decision,
                    "tool_calls": json.dumps(
                        [c.model_dump() for c in r.tool_calls], ensure_ascii=False
                    ),
                    "user_message": r.user_message,
                    "payload": d.attack.payload,
                    "human_attack_success": "",
                }
            )


def read_sheet(path: Path) -> dict[str, bool]:
    """Human labels from a filled sheet; yes/no/true/false/1/0, blanks rejected. Accepts the
    byte-order mark Excel adds when saving as "CSV UTF-8"."""
    labels: dict[str, bool] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            value = row["human_attack_success"].strip().lower()
            if value in ("yes", "y", "true", "1"):
                labels[row["key"]] = True
            elif value in ("no", "n", "false", "0"):
                labels[row["key"]] = False
            else:
                raise ValueError(
                    f"{row['key']}: human_attack_success must be yes or no, got {value!r}"
                )
    return labels
