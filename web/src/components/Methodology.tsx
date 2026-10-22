import { FlaskConical, Languages, Repeat, Scale, ServerCog, TriangleAlert } from "lucide-react";
import { headline, metric, per100, results, secondary } from "../data";
import { Reveal } from "../motion";

export function Methodology() {
  const sec = headline(secondary);
  const secNone = per100(metric(sec.find((r) => r.config === "a"), "asr_mean")?.value);
  const secBoundary = per100(metric(sec.find((r) => r.config === "d"), "asr_mean")?.value);
  const facts = [
    {
      icon: FlaskConical,
      title: "Paired test messages",
      text: `${results.n_docs} made-up messages: half normal, half the same message with one hidden attack added, so the two can be compared directly.`,
    },
    {
      icon: Languages,
      title: "Three languages",
      text: "English, Telugu script and Telugu-English mix, with 6 kinds of tricks and 3 attacker goals.",
    },
    {
      icon: Repeat,
      title: `${results.trials} tries each`,
      text: "AI answers vary a little run to run, so every message was tried three times in every setup.",
    },
    {
      icon: Scale,
      title: "Honest error bars",
      text: "The 95% ranges come from resampling whole messages 2,000 times, not from treating tries as independent.",
    },
    {
      icon: ServerCog,
      title: "Checked on a second model",
      text:
        secNone != null && secBoundary != null
          ? `On a larger AI model the same pattern held: ${secNone} in 100 attacks worked without protection, ${secBoundary} with the fact-checker.`
          : "A larger AI model was tested on a subset as a cross-check.",
    },
  ];
  const limits = [
    "The attacker used fixed tricks and did not adapt, so real attackers could do better.",
    "All messages are synthetic, and hidden text is simulated in the scanned text, not in real images.",
    "The payment rules are simple and fully written down, which suits the fact-checker design.",
    "One main AI model (Qwen3 8B, run locally); results may differ for other models.",
  ];

  return (
    <section id="method" aria-labelledby="method-title" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <h2 id="method-title" className="text-3xl font-bold tracking-tight text-ink-strong sm:text-4xl">
          How we made the numbers trustworthy
        </h2>
      </Reveal>
      <Reveal delay={0.05}>
        <ul className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {facts.map((f) => (
            <li key={f.title} className="rounded-2xl border border-line bg-surface p-5">
              <f.icon className="h-5 w-5 text-accent" aria-hidden="true" />
              <p className="mt-3 font-semibold text-ink-strong">{f.title}</p>
              <p className="mt-1 text-sm text-muted">{f.text}</p>
            </li>
          ))}
        </ul>
      </Reveal>
      <Reveal delay={0.1}>
        <div className="mt-6 rounded-2xl border border-line bg-surface-2/60 p-5 sm:p-6">
          <p className="flex items-center gap-2 font-semibold text-ink-strong">
            <TriangleAlert className="h-5 w-5 text-danger" aria-hidden="true" />
            Limits to keep in mind
          </p>
          <ul className="mt-3 list-disc space-y-1.5 pl-6 text-sm text-muted">
            {limits.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </div>
      </Reveal>
    </section>
  );
}
