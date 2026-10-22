// Mirrors the Pydantic models WebRun / WebConfigRow / WebExample in src/injbench/schema.py.
// The JSON is produced by `uv run injbench export-web`; never edit it by hand.

export type ConfigId = "a" | "b" | "c" | "d" | "e";

export interface MetricValue {
  value: number | null;
  lo: number | null;
  hi: number | null;
  n_docs: number;
}

export interface ConfigRow {
  config: ConfigId;
  name: string;
  what: string;
  group: string; // "all" | "family=F1_override" | "goal=G1_force_approve" | "lang=en"
  metrics: Record<string, MetricValue>;
}

export interface Run {
  run_id: string;
  model_ids: string[];
  n_docs: number;
  trials: number;
  n_records: number;
  threshold: number | null;
  run_date: string | null;
  rows: ConfigRow[];
}

export interface Action {
  text: string;
  attack_succeeded: boolean;
}

export interface Example {
  doc_id: string;
  family: string;
  family_name: string;
  goal: string;
  goal_name: string;
  lang: "en" | "te" | "te-en";
  message: string;
  hidden_from_humans: boolean;
  hidden_instruction: string;
  correct: string;
  actions: Partial<Record<ConfigId, Action>>;
}
