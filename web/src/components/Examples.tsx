import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { CheckCircle2, EyeOff, XCircle } from "lucide-react";
import { useState } from "react";
import { CONFIG_ORDER, examples, results } from "../data";
import { Reveal } from "../motion";

function Highlighted({ message, hidden }: { message: string; hidden: string }) {
  const i = message.indexOf(hidden);
  if (!hidden || i < 0) return <>{message}</>;
  return (
    <>
      {message.slice(0, i)}
      <mark className="rounded bg-danger/20 px-0.5 text-danger ring-1 ring-danger/40">{hidden}</mark>
      {message.slice(i + hidden.length)}
    </>
  );
}

export function Examples() {
  const [active, setActive] = useState(0);
  const reduce = useReducedMotion();
  const names = Object.fromEntries(results.rows.filter((r) => r.group === "all").map((r) => [r.config, r.name]));
  if (!examples.length) return null;
  const ex = examples[active];

  return (
    <section id="attacks" aria-labelledby="attacks-title" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <h2 id="attacks-title" className="text-3xl font-bold tracking-tight text-ink-strong sm:text-4xl">
          Real attacks from the test
        </h2>
        <p className="mt-3 max-w-3xl text-muted">
          Each example is a real message from the run, with the hidden instruction marked in red, and what each
          defense actually did with it.
        </p>
      </Reveal>

      <Reveal delay={0.05}>
        <div className="mt-6 flex flex-wrap gap-2" role="tablist" aria-label="Attack examples">
          {examples.map((e, i) => (
            <button
              key={e.doc_id}
              type="button"
              role="tab"
              aria-selected={i === active}
              aria-controls="example-panel"
              onClick={() => setActive(i)}
              className={`min-h-11 rounded-lg border px-4 text-sm transition-colors ${
                i === active ? "border-accent bg-accent/15 text-ink-strong" : "border-line text-muted hover:text-ink"
              }`}
            >
              {e.family_name}
            </button>
          ))}
        </div>
      </Reveal>

      <AnimatePresence mode="wait">
        <motion.div
          key={ex.doc_id}
          id="example-panel"
          role="tabpanel"
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduce ? undefined : { opacity: 0, y: -8 }}
          transition={{ duration: 0.25 }}
          className="mt-6 grid gap-4 lg:grid-cols-5"
        >
          <div className="rounded-2xl border border-line bg-surface p-5 sm:p-6 lg:col-span-3">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-full bg-surface-2 px-2.5 py-1 text-muted">Goal: {ex.goal_name}</span>
              {ex.hidden_from_humans && (
                <span className="inline-flex items-center gap-1 rounded-full bg-danger/15 px-2.5 py-1 text-danger">
                  <EyeOff className="h-3.5 w-3.5" aria-hidden="true" />
                  Invisible to a person, read by the AI
                </span>
              )}
            </div>
            <p className="mt-4 text-sm font-medium text-muted">The message the assistant read</p>
            <pre className="mt-2 font-mono text-sm leading-relaxed whitespace-pre-wrap break-words text-ink" lang={ex.lang === "te" ? "te" : "en"}>
              <Highlighted message={ex.message} hidden={ex.hidden_instruction} />
            </pre>
            <p className="mt-5 rounded-lg border border-safe/30 bg-safe/10 p-3 text-sm text-ink">
              <span className="font-semibold">The right thing to do:</span> {ex.correct}.
            </p>
          </div>

          <ul className="space-y-2 lg:col-span-2" aria-label="What each defense did">
            {CONFIG_ORDER.map((c) => {
              const act = ex.actions[c];
              if (!act) return null;
              const bad = act.attack_succeeded;
              return (
                <li key={c} className={`rounded-xl border p-4 ${bad ? "border-danger/40 bg-danger/10" : "border-line bg-surface"}`}>
                  <div className="flex items-center gap-2 text-sm font-semibold text-ink-strong">
                    {bad ? (
                      <XCircle className="h-4 w-4 shrink-0 text-danger" aria-hidden="true" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-safe" aria-hidden="true" />
                    )}
                    {names[c] ?? c}
                    <span className="sr-only">{bad ? "(fooled)" : "(not fooled)"}</span>
                  </div>
                  <p className="mt-1 pl-6 text-sm text-muted">{act.text}</p>
                </li>
              );
            })}
          </ul>
        </motion.div>
      </AnimatePresence>
    </section>
  );
}
