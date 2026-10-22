import { useState } from "react";
import { headline, metric, per100, results, tau05 } from "../data";
import { BarTable, type BarRow } from "./BarTable";

const MODES = [
  { key: "asr_mean", label: "Every attack" },
  { key: "asr_twin_adjusted", label: "Only attacks that caused the mistake" },
] as const;

export function Results() {
  const [mode, setMode] = useState<(typeof MODES)[number]["key"]>("asr_mean");
  const rows = headline(results);
  const attackRows: BarRow[] = rows.map((r) => ({ config: r.config, name: r.name, m: metric(r, mode) }));
  const normalRows: BarRow[] = rows.map((r) => ({ config: r.config, name: r.name, m: metric(r, "benign_accuracy") }));
  const pgDefault = per100(metric(headline(tau05).find((r) => r.config === "c"), "asr_mean")?.value);
  const pgTuned = per100(metric(rows.find((r) => r.config === "c"), "asr_mean")?.value);

  return (
    <section id="results" aria-labelledby="results-title" className="section bg-band">
      <div className="wrapper">
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <p className="eyebrow">Results</p>
            <h2 id="results-title" className="mt-3 text-step-4 text-ink">
              Five defenses on the same messages
            </h2>
          </div>
          <p className="prose text-muted lg:col-span-5 lg:self-end">
            Each message went through every defense three times. The line across each bar is the 95% range; where two
            ranges overlap a lot, the difference could be chance.
          </p>
        </div>

        <div className="mt-10 inline-flex rounded-[var(--radius-control)] border border-line-strong p-0.5" role="group" aria-label="Which attacks to count">
          {MODES.map((m) => (
            <button
              key={m.key}
              type="button"
              aria-pressed={mode === m.key}
              onClick={() => setMode(m.key)}
              className={`min-h-10 rounded-[calc(var(--radius-control)-2px)] px-4 text-step--1 transition-colors duration-150 ${
                mode === m.key ? "bg-accent-subtle font-medium text-accent" : "text-muted hover:text-ink"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div className="mt-8 grid gap-12 lg:grid-cols-2 lg:gap-16">
          <BarTable
            caption="Attacks that worked, per 100"
            note={
              mode === "asr_mean"
                ? "Lower is better."
                : "Lower is better. Leaves out cases where the assistant made the same mistake without the attack."
            }
            rows={attackRows}
            highlight={["d"]}
          />
          <BarTable
            caption="Normal messages handled right, per 100"
            note="Higher is better. Blocking everything would score low here."
            rows={normalRows}
            highlight={["d"]}
          />
        </div>

        {pgDefault != null && pgTuned != null && (
          <p className="prose mt-10 border-l-2 border-line-strong pl-4 text-step--1 text-muted">
            Meta's attack detector reached <span className="num text-ink">{pgTuned} in 100</span> only after its
            sensitivity was tuned on separate practice data. At its default setting it let{" "}
            <span className="num text-ink">{pgDefault} in 100</span> attacks through, close to no protection at all.
          </p>
        )}
      </div>
    </section>
  );
}
