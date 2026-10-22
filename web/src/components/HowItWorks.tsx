import { ArrowRight, Bot, FileText, Gavel, ScanSearch, Wrench } from "lucide-react";
import { headline, results } from "../data";
import { Reveal } from "../motion";

const STEPS = [
  { icon: FileText, title: "A message arrives", text: "Bank text, receipt or chat, maybe with a hidden instruction." },
  { icon: ScanSearch, title: "A defense checks it", text: "One of the five setups below, or none." },
  { icon: Bot, title: "The AI assistant reads it", text: "The same AI model in every setup." },
  { icon: Wrench, title: "It acts", text: "Pay, hold, flag or do nothing. Payments are simulated." },
  { icon: Gavel, title: "We score it", text: "Fixed rules decide whether the attack worked. No AI judge." },
];

export function HowItWorks() {
  const rows = headline(results);
  return (
    <section id="how" aria-labelledby="how-title" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <h2 id="how-title" className="text-3xl font-bold tracking-tight text-ink-strong sm:text-4xl">How it works</h2>
      </Reveal>
      <Reveal delay={0.05}>
        <ol className="mt-8 grid gap-3 md:grid-cols-5">
          {STEPS.map((s, i) => (
            <li key={s.title} className="relative rounded-2xl border border-line bg-surface p-5">
              <s.icon className="h-6 w-6 text-accent" aria-hidden="true" />
              <p className="mt-3 font-semibold text-ink-strong">
                <span className="mr-1 font-mono text-muted">{i + 1}.</span>
                {s.title}
              </p>
              <p className="mt-1 text-sm text-muted">{s.text}</p>
              {i < STEPS.length - 1 && (
                <ArrowRight className="absolute top-1/2 -right-3 hidden h-5 w-5 -translate-y-1/2 text-line md:block" aria-hidden="true" />
              )}
            </li>
          ))}
        </ol>
      </Reveal>
      <Reveal delay={0.1}>
        <h3 className="mt-14 text-xl font-semibold text-ink-strong">The five defenses</h3>
        <ul className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((r) => (
            <li key={r.config} className="rounded-2xl border border-line bg-surface p-5">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ background: `var(--color-cfg-${r.config})` }} aria-hidden="true" />
                <p className="font-semibold text-ink-strong">{r.name}</p>
              </div>
              <p className="mt-2 text-sm text-muted">{r.what}</p>
            </li>
          ))}
        </ul>
      </Reveal>
    </section>
  );
}
