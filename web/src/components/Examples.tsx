import { EyeOff } from "lucide-react";
import { useRef, useState, type KeyboardEvent } from "react";
import { CONFIG_ORDER, examples, headline, results } from "../data";
import { Highlighted } from "./Highlighted";
import { Verdict } from "./Verdict";

export function Examples() {
  const [active, setActive] = useState(0);
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const names = Object.fromEntries(headline(results).map((r) => [r.config, r.name]));
  if (!examples.length) return null;
  const ex = examples[active];

  // Roving tabindex: one tab stop for the list; arrows, Home and End move between tabs.
  function onKey(e: KeyboardEvent) {
    const last = examples.length - 1;
    const next =
      e.key === "ArrowRight" || e.key === "ArrowDown"
        ? (active + 1) % examples.length
        : e.key === "ArrowLeft" || e.key === "ArrowUp"
          ? (active - 1 + examples.length) % examples.length
          : e.key === "Home"
            ? 0
            : e.key === "End"
              ? last
              : null;
    if (next == null) return;
    e.preventDefault();
    setActive(next);
    tabs.current[next]?.focus();
  }

  return (
    <section id="attacks" aria-labelledby="attacks-title" className="section bg-band">
      <div className="wrapper">
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <p className="eyebrow">Real attacks</p>
            <h2 id="attacks-title" className="mt-3 text-step-4 text-ink">
              Six kinds of trick, and what each defense did
            </h2>
          </div>
          <p className="prose text-muted lg:col-span-5 lg:self-end">
            Each example is a message from the test run. The hidden instruction is marked; the list shows what every
            defense actually did with it.
          </p>
        </div>

        <div className="mt-10 grid gap-8 lg:grid-cols-12 lg:gap-12">
          <div
            role="tablist"
            aria-label="Kinds of trick"
            aria-orientation="vertical"
            onKeyDown={onKey}
            className="flex gap-1 overflow-x-auto border-b border-line lg:col-span-3 lg:flex-col lg:overflow-visible lg:border-b-0 lg:border-l"
          >
            {examples.map((e, i) => {
              const on = i === active;
              return (
                <button
                  key={e.doc_id}
                  ref={(el) => {
                    tabs.current[i] = el;
                  }}
                  type="button"
                  role="tab"
                  id={`tab-${e.doc_id}`}
                  aria-selected={on}
                  aria-controls="example-panel"
                  tabIndex={on ? 0 : -1}
                  onClick={() => setActive(i)}
                  className={`-mb-px min-h-11 shrink-0 border-b-2 px-3 text-left text-step--1 whitespace-nowrap transition-colors duration-150 lg:-ml-px lg:mb-0 lg:border-b-0 lg:border-l-2 lg:whitespace-normal ${
                    on ? "border-accent font-medium text-ink" : "border-transparent text-muted hover:text-ink"
                  }`}
                >
                  {e.family_name}
                </button>
              );
            })}
          </div>

          <div
            id="example-panel"
            role="tabpanel"
            aria-labelledby={`tab-${ex.doc_id}`}
            tabIndex={0}
            className="grid gap-8 lg:col-span-9 lg:grid-cols-9"
          >
            <div className="rounded-[var(--radius-panel)] border border-line bg-surface lg:col-span-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3 text-step--1">
                <span className="text-muted">
                  Attacker’s goal: <span className="text-ink">{ex.goal_name}</span>
                </span>
                <span className="num text-muted">{ex.doc_id}</span>
              </div>
              {ex.hidden_from_humans && (
                <p className="flex items-center gap-2 border-b border-line px-5 py-2 text-step--1 text-danger">
                  <EyeOff className="size-4 shrink-0" aria-hidden="true" />
                  Invisible to a person, read by the AI
                </p>
              )}
              <pre
                className="px-5 pt-5 font-mono text-step--1 leading-relaxed break-words whitespace-pre-wrap text-ink"
                lang={ex.lang === "te" ? "te" : "en"}
              >
                <Highlighted message={ex.message} hidden={ex.hidden_instruction} />
              </pre>
              <p className="px-5 pt-4 pb-5 text-step--1 text-muted">
                Correct action: <span className="text-ink">{ex.correct}</span>.
              </p>
            </div>

            <ul className="space-y-5 lg:col-span-4" aria-label="What each defense did">
              {CONFIG_ORDER.map((c) => {
                const act = ex.actions[c];
                return act ? (
                  <li key={c}>
                    <Verdict name={names[c] ?? c} text={act.text} fooled={act.attack_succeeded} />
                  </li>
                ) : null;
              })}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
