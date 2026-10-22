import { headline, results } from "../data";

const STEPS = [
  ["A message arrives", "A bank text, receipt or chat message, sometimes with a hidden instruction inside."],
  ["A defense checks it", "One of the five setups below, or none at all."],
  ["The AI assistant reads it", "The same AI model sits behind every setup."],
  ["It acts", "Pay, hold, flag or do nothing. Payments are simulated; no money moves."],
  ["We score it", "Fixed rules decide whether the attack worked. No AI judges another AI."],
];

export function HowItWorks() {
  const rows = headline(results);
  return (
    <section id="how" aria-labelledby="how-title" className="section wrapper">
      <div className="grid gap-12 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-5">
          <p className="eyebrow">How it works</p>
          <h2 id="how-title" className="mt-3 text-step-4 text-ink">
            One assistant, five ways to protect it
          </h2>
          <ol className="mt-8 border-t border-line">
            {STEPS.map(([title, text], i) => (
              <li key={title} className="grid grid-cols-[2.5rem_1fr] border-b border-line py-4">
                <span className="num text-step--1 text-muted" aria-hidden="true">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <p className="font-medium text-ink">{title}</p>
                  <p className="mt-1 text-step--1 text-muted">{text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <div className="lg:col-span-7 lg:pt-16">
          <h3 className="text-step-2 text-ink">The five defenses</h3>
          <dl className="mt-6 divide-y divide-line border-y border-line">
            {rows.map((r) => (
              <div key={r.config} className="grid gap-1 py-4 sm:grid-cols-[14rem_1fr] sm:gap-6">
                <dt className={r.config === "d" ? "font-medium text-accent" : "font-medium text-ink"}>{r.name}</dt>
                <dd className="text-muted">{r.what}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}
