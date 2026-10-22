import { Bot, ClipboardCheck, CreditCard, FileText, ScanSearch, type LucideIcon } from "lucide-react";
import { headline, metric, per100, results } from "../data";
import { Stagger, StaggerItem } from "../motion";
import { SectionHeader } from "./SectionHeader";

const STEPS: [LucideIcon, string, string][] = [
  [FileText, "A message arrives", "A bank text, receipt or chat, sometimes with a hidden instruction inside."],
  [ScanSearch, "A defense checks it", "One of the five setups below, or none at all."],
  [Bot, "The AI reads it", "The same AI model sits behind every setup."],
  [CreditCard, "It acts", "Pay, hold, flag or do nothing. Payments are simulated."],
  [ClipboardCheck, "We score it", "Fixed rules decide if the attack worked. No AI judge."],
];

const SPAN: Record<string, string> = {
  a: "lg:col-span-2",
  b: "lg:col-span-2",
  c: "lg:col-span-2",
  d: "lg:col-span-4",
  e: "lg:col-span-2",
};

export function HowItWorks() {
  const rows = headline(results);
  return (
    <section id="how" aria-labelledby="how-title" className="section border-y border-line bg-band">
      <div className="wrapper">
        <SectionHeader
          id="how-title"
          eyebrow="How it works"
          title="One assistant, five ways to protect it"
          lead="Each message takes the same path. Only the defense in step two changes."
        />

        <Stagger>
          <ol className="mt-14 grid gap-4 md:grid-cols-5">
            {STEPS.map(([Icon, title, text], i) => (
              <li key={title} className="relative">
                {i < STEPS.length - 1 && (
                  <span
                    className="absolute top-7 left-[calc(50%+2.25rem)] hidden h-px w-[calc(100%-4.5rem+1rem)] bg-line-strong/60 md:block"
                    aria-hidden="true"
                  />
                )}
                <StaggerItem className="flex gap-4 md:flex-col md:items-center md:text-center">
                  <span className="relative grid size-14 shrink-0 place-items-center rounded-2xl border border-line bg-surface text-accent shadow-sm">
                    <Icon className="size-6" aria-hidden="true" />
                    <span className="num absolute -top-2 -right-2 grid size-6 place-items-center rounded-full bg-accent-solid text-sm font-semibold text-on-accent">
                      {i + 1}
                    </span>
                  </span>
                  <div>
                    <p className="font-semibold text-ink md:mt-1">{title}</p>
                    <p className="mt-1 text-sm text-muted">{text}</p>
                  </div>
                </StaggerItem>
              </li>
            ))}
          </ol>
        </Stagger>

        <h3 className="mt-20 text-2xl text-ink">The five defenses</h3>
        <Stagger>
        <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
          {rows.map((r) => {
            const v = metric(r, "asr_mean")?.value ?? null;
            const best = r.config === "d";
            return (
              <li key={r.config} className={`flex ${SPAN[r.config]} ${best ? "sm:col-span-2" : ""}`}>
                <StaggerItem
                  className={`card card-hover flex w-full flex-col p-6 ${best ? "border-accent/50 bg-accent-subtle" : ""}`}
                >
                <div className="flex items-start justify-between gap-3">
                  <p className={`text-lg font-semibold ${best ? "text-accent" : "text-ink"}`}>{r.name}</p>
                  {best && (
                    <span className="shrink-0 rounded-full bg-accent-solid px-2.5 py-0.5 text-sm font-medium text-on-accent">
                      Best result
                    </span>
                  )}
                </div>
                <p className={`mt-2 text-[0.9375rem] ${best ? "text-ink" : "text-muted"}`}>{r.what}</p>
                <div className="mt-auto pt-6">
                  <div className="flex items-baseline justify-between text-sm">
                    <span className="text-muted">Attacks that worked</span>
                    <span className="num font-semibold text-ink">{per100(v)} in 100</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-track" aria-hidden="true">
                    <div
                      className={`h-full rounded-full ${best ? "bg-accent" : "bg-bar"}`}
                      style={{ width: `${Math.max(1.5, (v ?? 0) * 100)}%` }}
                    />
                  </div>
                </div>
                </StaggerItem>
              </li>
            );
          })}
        </ul>
        </Stagger>
      </div>
    </section>
  );
}
