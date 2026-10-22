import { ArrowRight } from "lucide-react";
import { REPO_URL, examples, headline, metric, per100, results } from "../data";
import { Highlighted } from "./Highlighted";
import { Verdict } from "./Verdict";

export function Hero() {
  const rows = headline(results);
  const none = rows.find((r) => r.config === "a");
  const checker = rows.find((r) => r.config === "d");
  const from = per100(metric(none, "asr_mean")?.value);
  const to = per100(metric(checker, "asr_mean")?.value);
  const ex = examples.find((e) => e.family === "F1_override") ?? examples[0];

  return (
    <section id="top" className="wrapper grid gap-12 pt-12 pb-16 sm:pt-20 lg:grid-cols-12 lg:gap-16 lg:pb-24">
      <div className="lg:col-span-7">
        <p className="eyebrow">Prompt-injection benchmark · finance agent</p>
        <h1 className="mt-5 text-step-5 text-ink">
          A strict fact-checker cut successful attacks on an AI payment assistant from{" "}
          <span className="whitespace-nowrap tabular-nums">{from} in 100</span> to{" "}
          <span className="tabular-nums">{to}</span>.
        </h1>
        <p className="prose mt-6 text-step-1 text-muted">
          Attackers hide instructions inside bank texts, receipts and chat messages. We ran an AI assistant that reads
          those messages and decides whether to pay, put it behind five different defenses, and recorded what happened
          in {results.n_records.toLocaleString("en-IN")} trials.
        </p>
        <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-4">
          <a
            href="#results"
            className="inline-flex h-12 items-center gap-2 rounded-[var(--radius-control)] bg-accent px-5 font-medium text-on-accent transition-colors duration-150 hover:bg-accent-hover"
          >
            Read the results
            <ArrowRight className="size-4" aria-hidden="true" />
          </a>
          <a href={REPO_URL} className="link text-step-0">
            Code, data and full report on GitHub
          </a>
        </div>
      </div>

      {ex && (
        <figure className="self-end lg:col-span-5" aria-label="A real attack from the test">
          <div className="rounded-[var(--radius-panel)] border border-line bg-surface">
            <figcaption className="flex items-center justify-between border-b border-line px-5 py-3">
              <span className="eyebrow">Real message from the test</span>
              <span className="num text-step--1 text-muted">{ex.doc_id}</span>
            </figcaption>
            <p className="px-5 pt-5 font-mono text-step--1 leading-relaxed break-words whitespace-pre-wrap text-ink">
              <Highlighted message={ex.message} hidden={ex.hidden_instruction} />
            </p>
            <p className="px-5 pt-4 text-step--1 text-muted">
              Correct action: <span className="text-ink">{ex.correct}</span>.
            </p>
            <div className="mt-5 space-y-4 border-t border-line px-5 py-5">
              {ex.actions.a && <Verdict name="No protection" text={ex.actions.a.text} fooled={ex.actions.a.attack_succeeded} />}
              {ex.actions.d && <Verdict name="Strict fact-checker" text={ex.actions.d.text} fooled={ex.actions.d.attack_succeeded} />}
            </div>
          </div>
        </figure>
      )}
    </section>
  );
}
