import examplesJson from "./data/examples.json";
import resultsJson from "./data/results.json";
import secondaryJson from "./data/secondary.json";
import tau05Json from "./data/tau05.json";
import type { ConfigId, ConfigRow, Example, MetricValue, Run, TrialDoc } from "./types";

export const results = resultsJson as Run;
export const secondary = secondaryJson as Run;
export const tau05 = tau05Json as Run;
export const examples = examplesJson as Example[];

export const CONFIG_ORDER: ConfigId[] = ["a", "b", "c", "d", "e"];

// Validated categorical palette (dataviz checker, dark mode on #0B1120); fixed order everywhere.
export const CONFIG_COLOR: Record<ConfigId, string> = {
  a: "#3987e5",
  b: "#d95926",
  c: "#199e70",
  d: "#c98500",
  e: "#d55181",
};

export const REPO_URL = "https://github.com/mani-4444/Agent-Shield";
export const RELEASES_URL = `${REPO_URL}/releases`;

/** Every trial of the main run (about 0.8 MB); a separate chunk, loaded only by the trial browser. */
export function loadTrials(): Promise<TrialDoc[]> {
  return import("./data/trials.json").then((m) => m.default as TrialDoc[]);
}

/** Defense name without its parenthetical ("Attack detector (Meta Prompt Guard)" -> "Attack detector"). */
export function shortName(name: string): string {
  return name.replace(/\s*\(.*?\)/, "");
}

export function headline(run: Run): ConfigRow[] {
  return CONFIG_ORDER.flatMap((c) => run.rows.filter((r) => r.group === "all" && r.config === c));
}

export function groupRows(run: Run, dimension: "family" | "goal" | "lang"): ConfigRow[] {
  return run.rows.filter((r) => r.group.startsWith(`${dimension}=`));
}

export function metric(row: ConfigRow | undefined, key: string): MetricValue | undefined {
  return row?.metrics[key];
}

/** Everyday rounding for "x in 100" (2.5 -> 3), not banker's rounding. */
export function per100(value: number | null | undefined): number | null {
  return value == null ? null : Math.floor(value * 100 + 0.5);
}

export function pct(value: number | null | undefined, digits = 1): string {
  return value == null ? "–" : `${(value * 100).toFixed(digits)}%`;
}

export function ci(m: MetricValue | undefined): string {
  if (!m || m.lo == null || m.hi == null) return "";
  return `${(m.lo * 100).toFixed(1)} – ${(m.hi * 100).toFixed(1)}%`;
}
