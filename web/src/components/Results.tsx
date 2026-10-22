import { Gauge } from "lucide-react";
import { useState, type ReactNode } from "react";
import { headline, metric, per100, results, tau05 } from "../data";
import { Reveal } from "../motion";
import { BarTable, type BarRow } from "./BarTable";
import { ChoiceGroup } from "./ChoiceGroup";
import { Scatter } from "./Scatter";
import { SectionHeader } from "./SectionHeader";

type Mode = "asr_mean" | "asr_twin_adjusted";

function ChartCard({ title, note, action, children, className = "" }: { title: string; note: string; action?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <Reveal className={`card flex flex-col p-5 sm:p-7 ${className}`}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl text-ink">{title}</h3>
          <p className="mt-1 text-sm text-muted">{note}</p>
        </div>
        {action}
      </div>
      <div className="mt-6 flex-1">{children}</div>
    </Reveal>
  );
}

export function Results() {
  const [mode, setMode] = useState<Mode>("asr_mean");
  const rows = headline(results);
  const attackRows: BarRow[] = rows.map((r) => ({ config: r.config, name: r.name, m: metric(r, mode) }));
  const normalRows: BarRow[] = rows.map((r) => ({ config: r.config, name: r.name, m: metric(r, "benign_accuracy") }));
  const pgDefault = per100(metric(headline(tau05).find((r) => r.config === "c"), "asr_mean")?.value);
  const pgTuned = per100(metric(rows.find((r) => r.config === "c"), "asr_mean")?.value);
  const none = per100(metric(rows.find((r) => r.config === "a"), "asr_mean")?.value);

  return (
    <section id="results" aria-labelledby="results-title" className="section">
      <div className="wrapper">
        <SectionHeader
          id="results-title"
          eyebrow="Results"
          title={`Five defenses, the same ${results.n_docs} messages`}
          lead="Every message went through every defense three times. Lines across the bars and points are 95% ranges: if two ranges overlap a lot, the gap could be chance."
        />

        <div className="mt-14 grid gap-5 lg:grid-cols-12">
          <ChartCard
            className="lg:col-span-7"
            title="Safe and still useful"
            note="A good defense sits top-left: few attacks get through, and normal messages are still handled right."
          >
            <Scatter rows={rows} highlight={["d", "e"]} />
          </ChartCard>

          <ChartCard
            className="lg:col-span-5"
            title="Attacks that worked, per 100"
            note={
              mode === "asr_mean"
                ? "Lower is better."
                : "Lower is better. Leaves out cases where the assistant made the same mistake without the attack."
            }
          >
            <ChoiceGroup
              id="mode"
              label="Which attacks to count"
              value={mode}
              onChange={setMode}
              className="mb-4 w-full [&>button]:flex-1"
              options={[
                { value: "asr_mean", label: "Every attack" },
                { value: "asr_twin_adjusted", label: "Caused by the attack" },
              ]}
            />
            <BarTable caption="Attacks that worked, per 100" rows={attackRows} highlight={["d"]} />
          </ChartCard>

          <ChartCard
            className="lg:col-span-7"
            title="Normal messages handled right, per 100"
            note="Higher is better. A defense that blocked everything would score badly here."
          >
            <BarTable caption="Normal messages handled right, per 100" rows={normalRows} highlight={["d"]} />
          </ChartCard>

          {pgDefault != null && pgTuned != null && (
            <Reveal className="card card-hover flex flex-col p-5 sm:p-7 lg:col-span-5">
              <span className="grid size-10 place-items-center rounded-xl bg-accent-subtle text-accent" aria-hidden="true">
                <Gauge className="size-5" />
              </span>
              <h3 className="mt-5 text-xl text-ink">An off-the-shelf detector needs tuning</h3>
              <p className="mt-2 text-muted">
                Meta’s attack detector reached {pgTuned} in 100 only after its sensitivity was tuned on separate practice
                messages. At its default setting it let {pgDefault} in 100 through, close to the {none} with no
                protection at all.
              </p>
              <div className="mt-auto grid grid-cols-2 gap-3 pt-6">
                <div className="rounded-xl bg-surface-2 p-4">
                  <p className="num text-3xl font-semibold text-ink">{pgDefault}</p>
                  <p className="mt-1 text-sm text-muted">default setting</p>
                </div>
                <div className="rounded-xl bg-accent-subtle p-4">
                  <p className="num text-3xl font-semibold text-accent">{pgTuned}</p>
                  <p className="mt-1 text-sm text-muted">after tuning</p>
                </div>
              </div>
            </Reveal>
          )}
        </div>
      </div>
    </section>
  );
}
