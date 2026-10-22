import { headline, metric, per100, results } from "../data";

export function KeyFigures() {
  const rows = headline(results);
  const none = rows.find((r) => r.config === "a");
  const checker = rows.find((r) => r.config === "d");
  const figures = [
    { value: results.n_records.toLocaleString("en-IN"), label: "trials, every one scored by fixed rules" },
    { value: String(results.n_docs), label: "test messages, half carrying a hidden attack" },
    {
      value: `${per100(metric(none, "asr_mean")?.value)} → ${per100(metric(checker, "asr_mean")?.value)}`,
      label: "attacks that worked per 100, no protection vs fact-checker",
    },
    {
      value: `${per100(metric(checker, "benign_accuracy")?.value)}`,
      label: "normal messages per 100 the fact-checker still handled right",
    },
  ];
  return (
    <section aria-label="Key figures" className="wrapper">
      <dl className="grid grid-cols-1 border-y border-line sm:grid-cols-2 lg:grid-cols-4">
        {figures.map((f, i) => (
          <div
            key={f.label}
            className={`py-6 sm:px-6 ${i > 0 ? "border-t border-line sm:border-t-0" : ""} ${
              i % 2 === 1 ? "sm:border-l sm:border-line" : ""
            } ${i >= 2 ? "sm:border-t lg:border-t-0" : ""} ${i === 2 ? "lg:border-l lg:border-line" : ""} ${
              i === 0 ? "sm:pl-0" : ""
            }`}
          >
            <dt className="text-step--1 text-muted">{f.label}</dt>
            <dd className="num mt-2 text-step-3 text-ink">{f.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
