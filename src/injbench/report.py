"""Report (R8): summary.md, summary.csv, pareto.png, heatmap.png, gallery.md for one run.

Everything is derived from records.jsonl + the dataset named in run_config.json, so a replayed run
regenerates byte-identical summary.csv (no timestamps, paths or wall-clock values beyond records).
Charts follow the dataviz rules: one axis, fixed categorical order, direct labels, a single-hue
sequential ramp for the heatmap, recessive grid.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from itertools import pairwise
from pathlib import Path

from injbench import detectors
from injbench.metrics import HEADLINE, LOW_N, summarize
from injbench.runner import RECORDS, load_records
from injbench.schema import Document, MetricValue, Profile, RunRecord, SummaryRow

CONFIG_LABELS = {
    "a": "(a) none",
    "b": "(b) spotlight",
    "c": "(c) Prompt Guard",
    "d": "(d) boundary",
    "e": "(e) PG + boundary",
}
SERIES = {"a": "#2a78d6", "b": "#eb6834", "c": "#1baf7a", "d": "#eda100", "e": "#e87ba4"}
INK, INK_2, MUTED, GRID, AXIS, SURFACE = (
    "#0b0b0b",
    "#52514e",
    "#898781",
    "#e1e0d9",
    "#c3c2b7",
    "#fcfcfb",
)
RAMP = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
FAMILIES = ["F1_override", "F2_roleplay", "F3_hidden", "F4_multilingual", "F5_toolarg", "F6_exfil"]
TABLE_METRICS = [
    ("asr_mean", "ASR mean", True),
    ("asr_worst", "ASR worst-of-3", True),
    ("benign_accuracy", "Benign acc.", True),
    ("utility_strict", "Strict utility", True),
    ("utility_safe", "Safe utility", True),
    ("classifier_fpr", "Classifier FPR", True),
    ("delta_latency_p50", "Δ p50 latency ms", False),
    ("tokens_per_doc", "Tokens/trial", False),
]
GALLERY_PER_CONFIG = 5


# --- loading ------------------------------------------------------------------------------------


def load_run(run_dir: Path) -> tuple[list[RunRecord], dict[str, Document], dict[str, Profile]]:
    cfg = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
    data_dir = Path(cfg["data_dir"])
    docs: dict[str, Document] = {}
    for split in ("test", "dev"):
        path = data_dir / f"{split}.jsonl"
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line:
                    d = Document.model_validate_json(line)
                    docs[d.doc_id] = d
    profiles = {}
    for line in (data_dir / "profiles.jsonl").read_text(encoding="utf-8").splitlines():
        if line:
            p = Profile.model_validate_json(line)
            profiles[p.profile_id] = p
    return load_records(run_dir / RECORDS), docs, profiles


# --- tables -------------------------------------------------------------------------------------


def _num(x: float | None) -> str:
    return "" if x is None else f"{x:.6f}".rstrip("0").rstrip(".") or "0"


def summary_csv(rows: Sequence[SummaryRow]) -> str:
    names = [m.name for m in HEADLINE] + ["delta_latency_p50"]
    header = ["config", "group"] + [
        f"{n}_{k}" for n in names for k in ("value", "lo", "hi", "n_docs")
    ]
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        cells = [row.config, row.group]
        for n in names:
            m = row.metrics.get(n)
            cells += (
                ["", "", "", ""]
                if m is None
                else [_num(m.value), _num(m.lo), _num(m.hi), str(m.n_docs)]
            )
        writer.writerow(cells)
    return buf.getvalue()


def _int(x: float) -> str:
    """Rounded integer text without a "-0"."""
    return str(round(x))


def _cell(m: MetricValue | None, pct: bool) -> str:
    if m is None or m.value is None:
        return "–"
    scale, unit = (100, "%") if pct else (1, "")
    text = f"{m.value * scale:.1f}{unit}" if pct else _int(m.value)
    if m.lo is not None and m.hi is not None:
        text += (
            f" [{m.lo * scale:.1f}, {m.hi * scale:.1f}]"
            if pct
            else f" [{_int(m.lo)}, {_int(m.hi)}]"
        )
    if m.n_docs < LOW_N:
        text += " (low n)"
    return text


def summary_md(rows: Sequence[SummaryRow], records: Sequence[RunRecord], run_dir: Path) -> str:
    headline = [r for r in rows if r.group == "all"]
    trials = len({r.trial for r in records})
    lines = [
        f"# InjectionBench results: {run_dir.name}",
        "",
        f"{len(records)} records · {len({r.doc_id for r in records})} documents · "
        f"{trials} trial(s) per "
        f"(config, document) · models: {', '.join(sorted({r.model_id for r in records}))}.",
        "Values are point estimates with 95% cluster-bootstrap CIs over documents. "
        f"Cells built on fewer than {LOW_N} documents are marked (low n).",
        "",
        "## Headline",
        "",
        "| Config | " + " | ".join(label for _, label, _ in TABLE_METRICS) + " |",
        "|---|" + "---|" * len(TABLE_METRICS),
    ]
    has_classifier = {r.config for r in records if r.classifier_score is not None}
    for r in headline:
        cells = [
            "n/a"
            if key == "classifier_fpr" and r.config not in has_classifier
            else _cell(r.metrics.get(key), pct)
            for key, _, pct in TABLE_METRICS
        ]
        lines.append(f"| {CONFIG_LABELS.get(r.config, r.config)} | " + " | ".join(cells) + " |")
    for dimension, title in (
        ("family", "Attack success by family"),
        ("goal", "Attack success by goal"),
        ("lang", "Attack success by document language"),
    ):
        groups = sorted({r.group for r in rows if r.group.startswith(dimension + "=")})
        if not groups:
            continue
        configs = [r.config for r in headline]
        lines += [
            "",
            f"## {title} (ASR mean)",
            "",
            "| Group | " + " | ".join(CONFIG_LABELS.get(c, c) for c in configs) + " |",
            "|---|" + "---|" * len(configs),
        ]
        index = {(r.config, r.group): r for r in rows}
        for g in groups:
            cells = [
                _cell(index[(c, g)].metrics.get("asr_mean") if (c, g) in index else None, True)
                for c in configs
            ]
            lines.append(f"| {g.split('=', 1)[1]} | " + " | ".join(cells) + " |")
    errors = sum(r.error is not None for r in records)
    lines += [
        "",
        f"Records with errors: {errors}. Charts: `pareto.png`, `heatmap.png`. "
        "Failures: `gallery.md`.",
        "",
    ]
    return "\n".join(lines)


# --- charts -------------------------------------------------------------------------------------


def _axes_style(ax: object) -> None:
    ax.set_facecolor(SURFACE)  # type: ignore[attr-defined]
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)  # type: ignore[attr-defined]
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)  # type: ignore[attr-defined]
    ax.tick_params(colors=MUTED, labelcolor=INK_2)  # type: ignore[attr-defined]
    ax.grid(color=GRID, linewidth=0.8)  # type: ignore[attr-defined]
    ax.set_axisbelow(True)  # type: ignore[attr-defined]


def _pct(v: float | None, default: float) -> float:
    return (default if v is None else v) * 100


def spread_labels(ys: list[float], min_gap: float) -> list[float]:
    """Label y positions, in input order, nudged apart by at least min_gap (keeps sorted order)."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    placed = list(ys)
    for prev, cur in pairwise(order):
        placed[cur] = max(placed[cur], placed[prev] + min_gap)
    return placed


def pareto_png(rows: Sequence[SummaryRow], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    points = []
    for r in (r for r in rows if r.group == "all"):
        x, y = r.metrics["benign_accuracy"], r.metrics["asr_mean"]
        if x.value is not None and y.value is not None:
            points.append((r.config, x, y))
    fig, ax = plt.subplots(figsize=(7.5, 5), dpi=150, facecolor=SURFACE)
    _axes_style(ax)
    if points:
        xs_lo = min(_pct(x.lo, x.value or 0) for _, x, _ in points)
        ys_hi = max(_pct(y.hi, y.value or 0) for _, _, y in points)
        x_min, y_max = max(0.0, xs_lo - 8), min(105.0, ys_hi + 8)
        ax.set_xlim(x_min, 101.5)
        ax.set_ylim(0, y_max)
        gap = 0.06 * y_max
        label_ys = spread_labels([_pct(y.value, 0) for _, _, y in points], gap)
        for (config, x, y), ly in zip(points, label_ys, strict=True):
            cx, cy = _pct(x.value, 0), _pct(y.value, 0)
            color = SERIES.get(config, INK_2)
            ax.errorbar(
                cx,
                cy,
                xerr=[[cx - _pct(x.lo, x.value or 0)], [_pct(x.hi, x.value or 0) - cx]],
                yerr=[[cy - _pct(y.lo, y.value or 0)], [_pct(y.hi, y.value or 0) - cy]],
                fmt="o",
                ms=9,
                color=color,
                ecolor=color,
                elinewidth=2,
                capsize=0,
                markeredgecolor=SURFACE,
                markeredgewidth=2,
                zorder=3,
            )
            # Labels sit left of the point (accuracy clusters near 100%); a leader line when nudged.
            ax.annotate(
                CONFIG_LABELS.get(config, config),
                (cx, cy),
                xytext=(cx - 1.2, ly),
                textcoords="data",
                ha="right",
                va="center",
                color=INK,
                fontsize=9,
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.8}
                if abs(ly - cy) > 0.5
                else None,
            )
    ax.set_xlabel("Benign accuracy (%)  →  better", color=INK_2)
    ax.set_ylabel("Attack success rate, mean of trials (%)  ↓  better", color=INK_2)
    ax.set_title(
        "Utility vs. attack success per defense (95% CI)", color=INK, loc="left", fontsize=11
    )
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE, metadata={"Software": None})
    plt.close(fig)


def heatmap_png(rows: Sequence[SummaryRow], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Rectangle

    configs = [r.config for r in rows if r.group == "all"]
    index = {(r.config, r.group): r.metrics.get("asr_mean") for r in rows}
    fig, ax = plt.subplots(figsize=(1.4 * len(configs) + 2.5, 4.6), dpi=150, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    cmap = LinearSegmentedColormap.from_list("seq_blue", RAMP)
    for i, fam in enumerate(FAMILIES):
        for j, c in enumerate(configs):
            m = index.get((c, f"family={fam}"))
            if m is None or m.value is None:
                ax.add_patch(Rectangle((j, i), 0.96, 0.96, color=GRID))
                ax.text(j + 0.48, i + 0.48, "–", ha="center", va="center", color=MUTED)
                continue
            ax.add_patch(Rectangle((j, i), 0.96, 0.96, color=cmap(m.value)))
            ink = SURFACE if m.value > 0.5 else INK
            label = f"{m.value * 100:.0f}%" + ("\nlow n" if m.n_docs < LOW_N else "")
            ax.text(j + 0.48, i + 0.48, label, ha="center", va="center", color=ink, fontsize=9)
    ax.set_xlim(0, len(configs))
    ax.set_ylim(len(FAMILIES), 0)
    ax.set_xticks(
        [j + 0.48 for j in range(len(configs))],
        [CONFIG_LABELS.get(c, c) for c in configs],
        rotation=20,
        ha="right",
        color=INK_2,
        fontsize=9,
    )
    ax.set_yticks([i + 0.48 for i in range(len(FAMILIES))], FAMILIES, color=INK_2, fontsize=9)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_title("Attack success rate by family × defense", color=INK, loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE, metadata={"Software": None})
    plt.close(fig)


# --- gallery ------------------------------------------------------------------------------------


def _failure_rank(r: RunRecord, d: Document, p: Profile) -> int | None:
    """0 = attack succeeded, 1 = poisoned doc decided wrongly, 2 = benign doc decided wrongly."""
    if detectors.attack_success(r, d, p):
        return 0
    if d.attack is not None and detectors.any_deviation(r, d, p):
        return 1
    if d.attack is None and not detectors.decision_correct(r, d, p):
        return 2
    return None


def _excerpt(text: str, limit: int = 400) -> str:
    text = text.replace("\u200b", "<ZWSP>").replace("```", "'''")
    return text if len(text) <= limit else text[:limit] + " …"


def _calls(r: RunRecord) -> str:
    parts = [f"{t.name}({json.dumps(t.args, ensure_ascii=False)})" for t in r.tool_calls]
    return ", ".join(parts) or "none"


def gallery_md(
    records: Sequence[RunRecord], docs: Mapping[str, Document], profiles: Mapping[str, Profile]
) -> str:
    lines = [
        "# Failure gallery",
        "",
        "Attack successes first, then wrong decisions on poisoned, then benign docs.",
        "",
    ]
    for c in sorted({r.config for r in records}):
        ranked = []
        for r in records:
            if r.config != c:
                continue
            d = docs[r.doc_id]
            rank = _failure_rank(r, d, profiles[d.profile_id])
            if rank is not None:
                ranked.append((rank, r.key, r))
        ranked.sort(key=lambda t: (t[0], t[1]))
        lines += [f"## Config {c} {CONFIG_LABELS.get(c, '')[3:]}".rstrip(), ""]
        if not ranked:
            lines += ["No failures in this run.", ""]
        for rank, _, r in ranked[:GALLERY_PER_CONFIG]:
            d = docs[r.doc_id]
            p = profiles[d.profile_id]
            kind = ["attack succeeded", "wrong decision (poisoned)", "wrong decision (benign)"][
                rank
            ]
            lines += [f"### {r.key}: {kind}", ""]
            if d.attack:
                lines.append(
                    f"- Attack: {d.attack.family} / {d.attack.goal}, position {d.attack.position}"
                )
                lines.append(f"- Payload: `{_excerpt(d.attack.payload, 200)}`")
            lines += [
                f"- Gold: {d.gold_decision} · Decision: {r.decision}"
                + (" · blocked by classifier" if r.blocked_by_classifier else ""),
                f"- Tool calls: {_calls(r)}",
                f"- Detectors: attack_success={detectors.attack_success(r, d, p)}, "
                f"canary_leaked={detectors.canary_leaked(r, d, p)}, "
                f"decision_correct={detectors.decision_correct(r, d, p)}",
            ]
            if r.error:
                lines.append(f"- Error: {r.error}")
            lines += ["", "Agent-visible text:", "", "```text", _excerpt(d.ocr_text), "```", ""]
    return "\n".join(lines)


# --- entry point --------------------------------------------------------------------------------


def write_report(run_dir: Path, *, n_boot: int = 2000, seed: int = 2026) -> list[Path]:
    records, docs, profiles = load_run(run_dir)
    if not records:
        raise ValueError(f"no records in {run_dir}")
    rows = summarize(records, docs, profiles, n_boot=n_boot, seed=seed)
    outputs = {
        "summary.csv": summary_csv(rows),
        "summary.md": summary_md(rows, records, run_dir),
        "gallery.md": gallery_md(records, docs, profiles),
    }
    for name, text in outputs.items():
        (run_dir / name).write_text(text, encoding="utf-8", newline="\n")
    pareto_png(rows, run_dir / "pareto.png")
    heatmap_png(rows, run_dir / "heatmap.png")
    return [run_dir / n for n in (*outputs, "pareto.png", "heatmap.png")]
