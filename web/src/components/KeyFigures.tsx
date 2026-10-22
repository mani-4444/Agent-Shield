import { headline, metric, per100, results } from "../data";
import { Reveal } from "../motion";

export function KeyFigures() {
  const rows = headline(results);
  const none = rows.find((r) => r.config === "a");
  const checker = rows.find((r) => r.config === "d");
  const figures = [
    {
      value: (
        <>
          <span className="text-muted">{per100(metric(none, "asr_mean")?.value)}</span>
          <span className="mx-2 text-muted" aria-hidden="true">
            →
          </span>
          <span className="sr-only"> to </span>
          <span className="text-accent">{per100(metric(checker, "asr_mean")?.value)}</span>
        </>
      ),
      label: "attacks that worked per 100: no protection vs the strict fact-checker",
    },
    {
      value: <span className="text-accent">{per100(metric(checker, "benign_accuracy")?.value)}</span>,
      label: "normal messages per 100 the fact-checker still handled correctly",
    },
    { value: results.n_records.toLocaleString("en-IN"), label: "trials, each scored by fixed rules, no AI judge" },
    { value: String(results.n_docs), label: "test messages in English, Telugu and a mix of both" },
  ];
  return (
    <section aria-label="Key figures" className="wrapper">
      <Reveal>
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {figures.map((f) => (
            <div key={f.label} className="card flex flex-col-reverse justify-end gap-3 p-6">
              <dt className="text-sm text-muted">{f.label}</dt>
              <dd className="num text-metric font-semibold text-ink">{f.value}</dd>
            </div>
          ))}
        </dl>
      </Reveal>
    </section>
  );
}
