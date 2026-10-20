"""InjectionBench dashboard (R9): Results, Explorer, Live demo.

Run: uv run streamlit run app/dashboard.py
Replay is the default everywhere: nothing calls a provider unless the Live toggle is switched on.
Works with no results or data present (shows what to run instead).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from injbench import detectors
from injbench.schema import Document, Profile, RunRecord

RESULTS = Path("results")
DATA = Path("data/v1")
CONFIG_LABELS = {
    "a": "(a) none",
    "b": "(b) spotlight",
    "c": "(c) Prompt Guard",
    "d": "(d) boundary",
    "e": "(e) PG + boundary",
}


@st.cache_data(show_spinner=False)
def list_runs() -> list[str]:
    if not RESULTS.is_dir():
        return []
    return sorted(p.name for p in RESULTS.iterdir() if (p / "records.jsonl").is_file())


@st.cache_data(show_spinner=False)
def load_jsonl_docs(path: str) -> dict[str, Document]:
    p = Path(path)
    if not p.is_file():
        return {}
    docs = (
        Document.model_validate_json(x) for x in p.read_text(encoding="utf-8").splitlines() if x
    )
    return {d.doc_id: d for d in docs}


@st.cache_data(show_spinner=False)
def load_profiles(data_dir: str) -> dict[str, Profile]:
    p = Path(data_dir) / "profiles.jsonl"
    if not p.is_file():
        return {}
    profiles = (
        Profile.model_validate_json(x) for x in p.read_text(encoding="utf-8").splitlines() if x
    )
    return {x.profile_id: x for x in profiles}


@st.cache_data(show_spinner=False)
def load_run(run_id: str) -> tuple[list[RunRecord], str]:
    from injbench.runner import load_records

    run = RESULTS / run_id
    cfg_path = run / "run_config.json"
    data_dir = (
        json.loads(cfg_path.read_text(encoding="utf-8")).get("data_dir", str(DATA))
        if cfg_path.is_file()
        else str(DATA)
    )
    return load_records(run / "records.jsonl"), data_dir


def all_docs(data_dir: str) -> dict[str, Document]:
    return {**load_jsonl_docs(f"{data_dir}/test.jsonl"), **load_jsonl_docs(f"{data_dir}/dev.jsonl")}


# --- tabs -----------------------------------------------------------------------------------------


def results_tab() -> None:
    runs = list_runs()
    if not runs:
        st.info(
            "No runs yet. Try `uv run injbench eval --config all --split dev --trials 1 "
            "--limit 5 --run-id smoke` "
            "then `uv run injbench report --run results/smoke`."
        )
        return
    run_id = st.selectbox("Run", runs, index=len(runs) - 1, key="results_run")
    run = RESULTS / run_id
    summary = run / "summary.md"
    if not summary.is_file():
        st.warning(f"No report yet: run `uv run injbench report --run results/{run_id}`.")
        return
    cols = st.columns(2)
    for col, name, caption in (
        (cols[0], "pareto.png", "Utility vs attack success"),
        (cols[1], "heatmap.png", "Attack success by family"),
    ):
        if (run / name).is_file():
            col.image(str(run / name), caption=caption, use_container_width=True)
    csv_path = run / "summary.csv"
    if csv_path.is_file():
        table = pd.read_csv(csv_path)
        headline = table[table["group"] == "all"]
        keep = [
            "config",
            "asr_mean_value",
            "asr_worst_value",
            "benign_accuracy_value",
            "utility_strict_value",
            "classifier_fpr_value",
            "delta_latency_p50_value",
        ]
        st.dataframe(headline[[c for c in keep if c in headline.columns]], hide_index=True)
    st.markdown(summary.read_text(encoding="utf-8"))


def explorer_tab() -> None:
    runs = list_runs()
    if not runs:
        st.info("No runs to explore yet.")
        return
    run_id = st.selectbox("Run", runs, index=len(runs) - 1, key="explorer_run")
    records, data_dir = load_run(run_id)
    docs, profiles = all_docs(data_dir), load_profiles(data_dir)
    if not docs or not profiles:
        st.warning(f"Dataset {data_dir} not found; regenerate it with `uv run injbench data`.")
        return
    poisoned = [docs[r.doc_id] for r in records if r.doc_id in docs and docs[r.doc_id].attack]
    c1, c2, c3, c4 = st.columns(4)
    configs = c1.multiselect("Config", sorted({r.config for r in records}), key="ex_cfg")
    families = c2.multiselect(
        "Family", sorted({d.attack.family for d in poisoned if d.attack}), key="ex_fam"
    )
    goals = c3.multiselect(
        "Goal", sorted({d.attack.goal for d in poisoned if d.attack}), key="ex_goal"
    )
    langs = c4.multiselect("Language", ["en", "te", "te-en"], key="ex_lang")
    rows = []
    for r in records:
        d = docs.get(r.doc_id)
        if d is None or (configs and r.config not in configs) or (langs and d.lang not in langs):
            continue
        if (families or goals) and (
            d.attack is None
            or (families and d.attack.family not in families)
            or (goals and d.attack.goal not in goals)
        ):
            continue
        p = profiles[d.profile_id]
        rows.append(
            {
                "key": r.key,
                "config": r.config,
                "doc": r.doc_id,
                "gold": d.gold_decision,
                "decision": r.decision,
                "attack_success": detectors.attack_success(r, d, p),
                "blocked": r.blocked_by_classifier,
                "error": r.error or "",
            }
        )
    st.caption(f"{len(rows)} trials")
    if not rows:
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, height=260)
    doc_id = st.selectbox("Document", sorted({row["doc"] for row in rows}), key="ex_doc")
    d = docs[doc_id]
    st.markdown(
        f"**{doc_id}** · {d.doc_type} · {d.lang} · gold **{d.gold_decision}**"
        + (f" · {d.attack.family} / {d.attack.goal}" if d.attack else " · benign")
    )
    left, right = st.columns(2)
    left.text_area("What a human sees", d.visible_text, height=160, disabled=True, key="ex_vis")
    right.text_area(
        "What the agent sees (OCR)",
        d.ocr_text.replace("\u200b", "<ZWSP>"),
        height=160,
        disabled=True,
        key="ex_ocr",
    )
    traces = [r for r in records if r.doc_id == doc_id and (not configs or r.config in configs)]
    for col, r in zip(st.columns(max(1, min(5, len(traces)))), traces[:5], strict=False):
        col.markdown(f"**{CONFIG_LABELS.get(r.config, r.config)}** · trial {r.trial}")
        col.write(f"Decision: {r.decision}")
        col.json([c.model_dump() for c in r.tool_calls], expanded=False)
        if r.user_message:
            col.caption(r.user_message[:300])


def live_tab() -> None:
    from injbench.agent import llm
    from injbench.defenses import build_defense

    st.caption(
        "Runs (a) and (e) on one document. Replay uses cached responses only; "
        "Live calls the provider "
        "and spends quota."
    )
    live = st.toggle("Live (calls the provider)", value=False, key="live_toggle")
    docs, profiles = all_docs(str(DATA)), load_profiles(str(DATA))
    if not docs or not profiles:
        st.info(
            "No dataset found. Generate it with `uv run injbench data --seed 2026 --out data/v1`."
        )
        return
    doc_id = st.selectbox("Document", sorted(docs), key="live_doc")
    doc = docs[doc_id]
    st.text_area("Agent-visible text", doc.ocr_text, height=140, disabled=True, key="live_text")
    if not st.button("Run (a) and (e)", key="live_run"):
        return
    llm.configure(replay=not live)
    for col, config in zip(st.columns(2), ("a", "e"), strict=True):
        col.markdown(f"**{CONFIG_LABELS[config]}**")
        try:
            record = build_defense(config).run(doc, profiles[doc.profile_id], 0)
        except (
            Exception
        ) as exc:  # replay miss, missing calibration, unpinned model: show, don't crash
            col.warning(f"{type(exc).__name__}: {exc}")
            continue
        p = profiles[doc.profile_id]
        col.metric("Decision", record.decision, help=f"gold {doc.gold_decision}")
        col.write(f"Attack succeeded: {detectors.attack_success(record, doc, p)}")
        col.json([c.model_dump() for c in record.tool_calls], expanded=True)
        if record.classifier_score is not None:
            col.caption(f"Classifier score {record.classifier_score:.3f}")


def main() -> None:
    st.set_page_config(page_title="InjectionBench", layout="wide")
    st.title("InjectionBench")
    st.caption(
        "Indirect prompt-injection benchmark for a document-reading finance agent · replay mode"
    )
    results, explorer, live = st.tabs(["Results", "Explorer", "Live demo"])
    with results:
        results_tab()
    with explorer:
        explorer_tab()
    with live:
        live_tab()


main()
