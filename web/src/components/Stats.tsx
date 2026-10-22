import { ShieldAlert, ShieldCheck, Target } from "lucide-react";
import type { ReactNode } from "react";
import { headline, metric, per100, results } from "../data";
import { CountUp, Reveal } from "../motion";

function StatCard(props: { icon: ReactNode; tone: string; value: number; label: string; note: string; delay: number }) {
  return (
    <Reveal delay={props.delay} className="h-full">
      <div className="relative h-full overflow-hidden rounded-2xl border border-line bg-surface p-6 sm:p-8">
        <div className={`absolute inset-x-0 top-0 h-1 ${props.tone}`} aria-hidden="true" />
        <div className="flex items-center gap-2 text-sm text-muted">
          {props.icon}
          {props.label}
        </div>
        <p className="mt-4 font-mono text-5xl font-semibold text-ink-strong sm:text-6xl">
          <CountUp value={props.value} />
          <span className="ml-2 text-xl text-muted sm:text-2xl">in 100</span>
        </p>
        <p className="mt-3 text-sm text-muted">{props.note}</p>
      </div>
    </Reveal>
  );
}

export function Stats() {
  const rows = headline(results);
  const none = rows.find((r) => r.config === "a");
  const best = [...rows].sort(
    (x, y) => (metric(x, "asr_mean")?.value ?? 1) - (metric(y, "asr_mean")?.value ?? 1),
  )[0];
  const noneAsr = per100(metric(none, "asr_mean")?.value) ?? 0;
  const bestAsr = per100(metric(best, "asr_mean")?.value) ?? 0;
  const bestAcc = per100(metric(best, "benign_accuracy")?.value) ?? 0;

  return (
    <section aria-labelledby="answer" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <h2 id="answer" className="text-sm font-semibold tracking-widest text-accent uppercase">
          The answer in three numbers
        </h2>
      </Reveal>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <StatCard
          delay={0}
          tone="bg-danger"
          icon={<ShieldAlert className="h-4 w-4 text-danger" aria-hidden="true" />}
          value={noneAsr}
          label="Attacks that worked, no protection"
          note="The assistant on its own followed the hidden instruction this often."
        />
        <StatCard
          delay={0.1}
          tone="bg-safe"
          icon={<ShieldCheck className="h-4 w-4 text-safe" aria-hidden="true" />}
          value={bestAsr}
          label={`With the best defense: ${best?.name ?? ""}`}
          note="Same messages, same AI model, with the defense switched on."
        />
        <StatCard
          delay={0.2}
          tone="bg-accent"
          icon={<Target className="h-4 w-4 text-accent" aria-hidden="true" />}
          value={bestAcc}
          label="Normal payments handled right"
          note="On messages with no attack, the protected assistant still did the right thing."
        />
      </div>
    </section>
  );
}
