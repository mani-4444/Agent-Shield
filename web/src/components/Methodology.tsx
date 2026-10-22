import { FlaskConical, Info, Languages, Lock, Repeat, Scale, ServerCog, type LucideIcon } from "lucide-react";
import { headline, metric, per100, results, secondary } from "../data";
import { Reveal, Stagger, StaggerItem } from "../motion";
import { SectionHeader } from "./SectionHeader";

export function Methodology() {
  const sec = headline(secondary);
  const secNone = per100(metric(sec.find((r) => r.config === "a"), "asr_mean")?.value);
  const secChecker = per100(metric(sec.find((r) => r.config === "d"), "asr_mean")?.value);
  const facts: [LucideIcon, string, string][] = [
    [
      FlaskConical,
      "Paired messages",
      `${results.n_docs} made-up messages: half normal, half the same message with one hidden attack added, so each pair compares directly.`,
    ],
    [Languages, "Three languages", "English, Telugu script and a Telugu-English mix, with six kinds of trick and three attacker goals."],
    [Repeat, `${results.trials} tries each`, "AI answers vary from run to run, so every message went through every setup three times."],
    [Scale, "Honest error bars", "95% ranges come from resampling whole messages 2,000 times, not from treating repeat tries as independent."],
    [Lock, "Rules fixed in advance", "Scoring rules and the test messages were frozen before the final run. All tuning used separate practice messages."],
    [
      ServerCog,
      "Checked on a second model",
      secNone != null && secChecker != null
        ? `On a larger AI model the pattern held: ${secNone} in 100 attacks worked without protection, ${secChecker} with the fact-checker.`
        : "A larger AI model was tested on a subset as a cross-check.",
    ],
  ];
  const limits = [
    "The attacker used fixed tricks and did not adapt, so a real attacker could do better.",
    "All messages are synthetic; hidden text is simulated in scanned text, not in real images.",
    "The payment rules are simple and fully written down, which suits the fact-checker design.",
    "One main AI model (Qwen3 8B, run locally); results may differ for other models.",
  ];

  return (
    <section id="method" aria-labelledby="method-title" className="section">
      <div className="wrapper">
        <SectionHeader
          id="method-title"
          eyebrow="Method and limits"
          title="Why you can trust the numbers, and where they stop"
        />

        <Stagger>
          <dl className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {facts.map(([Icon, term, text]) => (
              <StaggerItem key={term} className="card card-hover p-6">
                <span className="grid size-10 place-items-center rounded-xl bg-accent-subtle text-accent" aria-hidden="true">
                  <Icon className="size-5" />
                </span>
                <dt className="mt-4 text-lg font-semibold text-ink">{term}</dt>
                <dd className="mt-1.5 text-[0.9375rem] text-muted">{text}</dd>
              </StaggerItem>
            ))}
          </dl>
        </Stagger>

        <Reveal className="card mt-4 flex flex-col gap-4 p-6 sm:flex-row sm:p-8">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-surface-2 text-ink" aria-hidden="true">
            <Info className="size-5" />
          </span>
          <div>
            <h3 className="text-xl text-ink">Limits to keep in mind</h3>
            <ul className="mt-3 grid gap-x-10 gap-y-2 text-[0.9375rem] text-muted md:grid-cols-2">
              {limits.map((l) => (
                <li key={l} className="flex gap-2.5">
                  <span className="mt-2.5 size-1.5 shrink-0 rounded-full bg-line-strong" aria-hidden="true" />
                  {l}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
