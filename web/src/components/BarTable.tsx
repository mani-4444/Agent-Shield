import type { ConfigId, MetricValue } from "../types";

export interface BarRow {
  config: ConfigId;
  name: string;
  m: MetricValue | undefined;
}

/**
 * A data table drawn as a bar chart: each row has the defense, a bar with its 95% range, and the
 * value. Screen readers get a normal table; the bars are decoration over the same numbers.
 */
export function BarTable({
  caption,
  note,
  rows,
  highlight,
}: {
  caption: string;
  note: string;
  rows: BarRow[];
  highlight: ConfigId[];
}) {
  return (
    <figure>
      <table className="w-full border-collapse text-left">
        <caption className="mb-1 text-left font-serif text-step-1 text-ink">{caption}</caption>
        <thead>
          <tr>
            <td colSpan={3} className="pb-4 text-step--1 text-muted">
              {note}
            </td>
          </tr>
          <tr className="sr-only">
            <th scope="col">Defense</th>
            <th scope="col">Out of 100</th>
            <th scope="col">95% range</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ config, name, m }) => {
            const v = m?.value ?? null;
            const lo = m?.lo ?? v;
            const hi = m?.hi ?? v;
            const on = highlight.includes(config);
            return (
              <tr key={config} className="border-t border-line">
                <th scope="row" className={`w-[38%] py-3 pr-4 align-middle text-step--1 font-normal ${on ? "text-ink font-medium" : "text-muted"}`}>
                  {name}
                </th>
                <td className="py-3 align-middle" aria-hidden="true">
                  <div className="relative h-6 rounded-sm bg-track">
                    {v != null && (
                      <div
                        className={`absolute inset-y-0 left-0 rounded-sm ${on ? "bg-accent" : "bg-bar"}`}
                        style={{ width: `${Math.max(0.6, v * 100)}%` }}
                      />
                    )}
                    {lo != null && hi != null && (
                      <div
                        className="absolute top-1/2 h-px -translate-y-1/2 bg-ink"
                        style={{ left: `${lo * 100}%`, width: `${Math.max(0, (hi - lo) * 100)}%` }}
                      >
                        <span className="absolute -top-1.5 left-0 h-3 w-px bg-ink" />
                        <span className="absolute -top-1.5 right-0 h-3 w-px bg-ink" />
                      </div>
                    )}
                  </div>
                </td>
                <td className="w-24 py-3 pl-4 text-right align-middle">
                  <span className={`num text-step-0 ${on ? "text-ink font-medium" : "text-ink"}`}>
                    {v == null ? "–" : Math.floor(v * 100 + 0.5)}
                  </span>
                  {lo != null && hi != null && (
                    <span className="sr-only">
                      {" "}
                      (95% range {(lo * 100).toFixed(1)} to {(hi * 100).toFixed(1)})
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </figure>
  );
}
