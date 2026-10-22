import { motion, useReducedMotion } from "framer-motion";
import type { ConfigId, MetricValue } from "../types";

export interface BarRow {
  config: ConfigId;
  name: string;
  m: MetricValue | undefined;
}

/**
 * A data table drawn as a bar chart: each row shows the defense and its value, with a full-width
 * bar and 95% range underneath. Rows are laid out with CSS grid, so table roles are explicit to
 * keep screen readers reading it as a table; the bars are decoration over the same numbers.
 */
export function BarTable({ caption, rows, highlight }: { caption: string; rows: BarRow[]; highlight: ConfigId[] }) {
  const reduce = useReducedMotion();
  return (
    <table role="table" className="block w-full">
      <caption className="sr-only">{caption}</caption>
      <thead role="rowgroup" className="sr-only">
        <tr role="row">
          <th role="columnheader" scope="col">Defense</th>
          <th role="columnheader" scope="col">Out of 100</th>
        </tr>
      </thead>
      <tbody role="rowgroup" className="block space-y-5">
        {rows.map(({ config, name, m }, i) => {
          const v = m?.value ?? null;
          const lo = m?.lo ?? v;
          const hi = m?.hi ?? v;
          const on = highlight.includes(config);
          return (
            <tr key={config} role="row" className="grid grid-cols-[1fr_auto] items-baseline gap-x-4 gap-y-2">
              <th role="rowheader" scope="row" className={`text-left text-[0.9375rem] ${on ? "font-semibold text-ink" : "font-normal text-muted"}`}>
                {name}
              </th>
              <td role="cell" className="text-right">
                <span className={`num text-xl font-semibold ${on ? "text-accent" : "text-ink"}`}>
                  {v == null ? "–" : Math.floor(v * 100 + 0.5)}
                </span>
                {lo != null && hi != null && (
                  <span className="sr-only">
                    {" "}
                    (95% range {(lo * 100).toFixed(1)} to {(hi * 100).toFixed(1)})
                  </span>
                )}
              </td>
              <td className="col-span-2" aria-hidden="true">
                <div className="relative h-3 rounded-full bg-track">
                  {v != null && (
                    <motion.div
                      className={`absolute inset-y-0 left-0 origin-left rounded-full ${on ? "bg-accent" : "bg-bar"}`}
                      style={{ width: `${Math.max(1, v * 100)}%` }}
                      initial={reduce ? false : { scaleX: 0 }}
                      whileInView={{ scaleX: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: reduce ? 0 : i * 0.06 }}
                    />
                  )}
                  {lo != null && hi != null && (
                    <div
                      className="absolute top-1/2 h-0.5 -translate-y-1/2 bg-ink/80"
                      style={{ left: `${lo * 100}%`, width: `${Math.max(0, (hi - lo) * 100)}%` }}
                    >
                      <span className="absolute -top-[7px] left-0 h-4 w-0.5 rounded-full bg-ink/80" />
                      <span className="absolute -top-[7px] right-0 h-4 w-0.5 rounded-full bg-ink/80" />
                    </div>
                  )}
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
