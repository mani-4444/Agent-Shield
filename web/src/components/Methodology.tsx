import { headline, metric, per100, results, secondary } from "../data";

export function Methodology() {
  const sec = headline(secondary);
  const secNone = per100(metric(sec.find((r) => r.config === "a"), "asr_mean")?.value);
  const secChecker = per100(metric(sec.find((r) => r.config === "d"), "asr_mean")?.value);
  const facts: [string, string][] = [
    [
      "Paired messages",
      `${results.n_docs} made-up messages: half normal, half the same message with one hidden attack added, so each pair can be compared directly.`,
    ],
    ["Three languages", "English, Telugu script and Telugu-English mix, with six kinds of trick and three attacker goals."],
    [
      `${results.trials} tries each`,
      "AI answers vary a little from run to run, so every message went through every setup three times.",
    ],
    [
      "Honest error bars",
      "The 95% ranges come from resampling whole messages 2,000 times, not from treating repeat tries as independent.",
    ],
    [
      "Rules fixed in advance",
      "How attacks are scored, and which messages form the test, were frozen before the final run. Tuning used separate practice messages.",
    ],
    [
      "A second model",
      secNone != null && secChecker != null
        ? `On a larger AI model the same pattern held: ${secNone} in 100 attacks worked without protection, ${secChecker} with the fact-checker.`
        : "A larger AI model was tested on a subset as a cross-check.",
    ],
  ];
  const limits = [
    "The attacker used fixed tricks and did not adapt, so a real attacker could do better.",
    "All messages are synthetic, and hidden text is simulated in scanned text, not in real images.",
    "The payment rules are simple and fully written down, which suits the fact-checker design.",
    "One main AI model (Qwen3 8B, run locally); results may differ for other models.",
  ];

  return (
    <section id="method" aria-labelledby="method-title" className="section bg-band">
      <div className="wrapper grid gap-12 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-4">
          <p className="eyebrow">Method and limits</p>
          <h2 id="method-title" className="mt-3 text-step-4 text-ink">
            Why the numbers can be trusted, and where they stop
          </h2>
        </div>

        <div className="lg:col-span-8">
          <dl className="grid gap-x-10 gap-y-6 sm:grid-cols-2">
            {facts.map(([term, text]) => (
              <div key={term} className="border-t border-line pt-4">
                <dt className="font-medium text-ink">{term}</dt>
                <dd className="mt-1 text-step--1 text-muted">{text}</dd>
              </div>
            ))}
          </dl>

          <h3 className="mt-14 text-step-2 text-ink">Limits to keep in mind</h3>
          <ul className="prose mt-4 list-disc space-y-2 pl-5 text-muted marker:text-line-strong">
            {limits.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
