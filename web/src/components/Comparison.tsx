import { Table2, BarChart3 } from "lucide-react";
import { useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  ErrorBar,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CONFIG_COLOR, ci, headline, metric, pct, per100, results, tau05 } from "../data";
import { Reveal } from "../motion";
import type { ConfigRow } from "../types";

type Datum = { name: string; config: string; value: number; err: [number, number]; ciText: string; n: number };

function toData(rows: ConfigRow[], key: string): Datum[] {
  return rows.flatMap((r) => {
    const m = metric(r, key);
    if (!m || m.value == null) return [];
    const v = m.value * 100;
    return [
      {
        name: r.name,
        config: r.config,
        value: v,
        err: [v - (m.lo ?? m.value) * 100, (m.hi ?? m.value) * 100 - v] as [number, number],
        ciText: ci(m),
        n: m.n_docs,
      },
    ];
  });
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: Datum }[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm shadow-xl">
      <p className="font-semibold text-ink-strong">{d.name}</p>
      <p className="text-ink">{Math.floor(d.value + 0.5)} in 100</p>
      {d.ciText && <p className="text-xs text-muted">95% range: {d.ciText}</p>}
      <p className="text-xs text-muted">{d.n} messages</p>
    </div>
  );
}

type LabelProps = { x?: number; y?: number; width?: number; height?: number; index?: number };

/** Value label placed just past the end of the CI whisker, so the two never overlap. */
function ValueLabel({ x = 0, y = 0, width = 0, height = 0, index = 0, data }: LabelProps & { data: Datum[] }) {
  const d = data[index];
  if (!d) return null;
  const pxPerUnit = d.value > 0 ? width / d.value : 0;
  const end = x + width + d.err[1] * pxPerUnit;
  return (
    <text x={end + 10} y={y + height / 2} dy="0.35em" fill="#f8fafc" fontSize={14} fontWeight={600}>
      {Math.floor(d.value + 0.5)}
    </text>
  );
}

function HBar({ data, title, caption }: { data: Datum[]; title: string; caption: string }) {
  return (
    <figure className="rounded-2xl border border-line bg-surface p-5 sm:p-6">
      <figcaption>
        <p className="font-semibold text-ink-strong">{title}</p>
        <p className="text-sm text-muted">{caption}</p>
      </figcaption>
      <div className="mt-4 h-72" role="img" aria-label={`${title}: ${data.map((d) => `${d.name} ${Math.floor(d.value + 0.5)}`).join(", ")}`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 56, bottom: 4, left: 8 }} barCategoryGap={10}>
            <XAxis type="number" domain={[0, 100]} hide />
            <YAxis
              type="category"
              dataKey="name"
              width={150}
              tickLine={false}
              axisLine={false}
              tick={{ fill: "#cbd5e1", fontSize: 13 }}
            />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(148,163,184,0.08)" }} />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} isAnimationActive={false}>
              {data.map((d) => (
                <Cell key={d.config} fill={CONFIG_COLOR[d.config as keyof typeof CONFIG_COLOR]} />
              ))}
              <ErrorBar dataKey="err" direction="x" width={6} strokeWidth={1.5} stroke="#e2e8f0" />
              <LabelList
                dataKey="value"
                content={(props) => <ValueLabel {...(props as LabelProps)} data={data} />}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}

export function Comparison() {
  const [twinAdjusted, setTwinAdjusted] = useState(false);
  const [asTable, setAsTable] = useState(false);
  const rows = headline(results);
  const asrKey = twinAdjusted ? "asr_twin_adjusted" : "asr_mean";
  const pg05 = headline(tau05).find((r) => r.config === "c");

  return (
    <section id="results" aria-labelledby="results-title" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <h2 id="results-title" className="text-3xl font-bold tracking-tight text-ink-strong sm:text-4xl">
          Five defenses, side by side
        </h2>
        <p className="mt-3 max-w-3xl text-muted">
          Every message was run three times through each defense. The thin line on each bar is the 95% range: if two
          ranges overlap a lot, the difference may be luck.
        </p>
        <div className="mt-6 flex flex-wrap gap-2" role="group" aria-label="Chart options">
          <button
            type="button"
            aria-pressed={twinAdjusted}
            onClick={() => setTwinAdjusted((v) => !v)}
            className={`min-h-11 rounded-lg border px-4 text-sm transition-colors ${
              twinAdjusted ? "border-accent bg-accent/15 text-ink-strong" : "border-line text-muted hover:text-ink"
            }`}
          >
            Only count attacks that caused the mistake
          </button>
          <button
            type="button"
            aria-pressed={asTable}
            onClick={() => setAsTable((v) => !v)}
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-line px-4 text-sm text-muted transition-colors hover:text-ink"
          >
            {asTable ? <BarChart3 className="h-4 w-4" aria-hidden="true" /> : <Table2 className="h-4 w-4" aria-hidden="true" />}
            {asTable ? "Show as chart" : "Show as table"}
          </button>
        </div>
      </Reveal>

      <Reveal delay={0.1} className="mt-6">
        {asTable ? (
          <div className="overflow-x-auto rounded-2xl border border-line">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-surface-2 text-muted">
                <tr>
                  <th scope="col" className="px-4 py-3 font-medium">Defense</th>
                  <th scope="col" className="px-4 py-3 font-medium">Attacks that worked</th>
                  <th scope="col" className="px-4 py-3 font-medium">Normal messages handled right</th>
                  <th scope="col" className="px-4 py-3 font-medium">Normal messages blocked by mistake</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.config} className="border-t border-line">
                    <th scope="row" className="px-4 py-3 font-medium text-ink-strong">
                      <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{ background: `var(--color-cfg-${r.config})` }} aria-hidden="true" />
                      {r.name}
                    </th>
                    <td className="px-4 py-3 font-mono">{pct(metric(r, asrKey)?.value)} <span className="text-muted">({ci(metric(r, asrKey))})</span></td>
                    <td className="px-4 py-3 font-mono">{pct(metric(r, "benign_accuracy")?.value)}</td>
                    <td className="px-4 py-3 font-mono">
                      {metric(r, "classifier_fpr") && r.config !== "a" && r.config !== "b" && r.config !== "d"
                        ? pct(metric(r, "classifier_fpr")?.value)
                        : "n/a"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            <HBar
              data={toData(rows, asrKey)}
              title="Attacks that worked, out of 100"
              caption={twinAdjusted ? "Excludes mistakes the AI also made without the attack. Lower is better." : "Lower is better."}
            />
            <HBar
              data={toData(rows, "benign_accuracy")}
              title="Normal messages handled right, out of 100"
              caption="Higher is better. A defense that blocks everything would score low here."
            />
          </div>
        )}
      </Reveal>

      {pg05 && (
        <Reveal delay={0.15}>
          <p className="mt-6 rounded-xl border border-line bg-surface-2/60 p-4 text-sm text-muted">
            <span className="font-semibold text-ink">About the attack detector:</span> it only works this well because
            its sensitivity was tuned on separate practice data. At Meta's default setting it let{" "}
            <span className="font-mono text-ink">{per100(metric(pg05, "asr_mean")?.value)} in 100</span> attacks through,
            about the same as no protection.
          </p>
        </Reveal>
      )}
    </section>
  );
}
