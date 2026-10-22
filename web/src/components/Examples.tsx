import { CircleCheck } from "lucide-react";
import { useRef, useState, type KeyboardEvent } from "react";
import { CONFIG_ORDER, examples, headline, results } from "../data";
import { Reveal } from "../motion";
import { PhoneMessage } from "./PhoneMessage";
import { SectionHeader } from "./SectionHeader";
import { Verdict } from "./Verdict";

export function Examples() {
  const [active, setActive] = useState(0);
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const names = Object.fromEntries(headline(results).map((r) => [r.config, r.name]));
  if (!examples.length) return null;
  const ex = examples[active];

  // Roving tabindex: one tab stop for the list; arrows, Home and End move between tabs.
  function onKey(e: KeyboardEvent) {
    const n = examples.length;
    const next =
      e.key === "ArrowRight" || e.key === "ArrowDown"
        ? (active + 1) % n
        : e.key === "ArrowLeft" || e.key === "ArrowUp"
          ? (active - 1 + n) % n
          : e.key === "Home"
            ? 0
            : e.key === "End"
              ? n - 1
              : null;
    if (next == null) return;
    e.preventDefault();
    setActive(next);
    tabs.current[next]?.focus();
  }

  return (
    <section id="attacks" aria-labelledby="attacks-title" className="section">
      <div className="wrapper">
        <SectionHeader
          id="attacks-title"
          eyebrow="Real attacks"
          title="Six kinds of trick, and what each defense did"
          lead="Every example is a message from the test run. The hidden instruction is marked in red."
        />

        <Reveal className="mt-12">
          <div role="tablist" aria-label="Kinds of trick" onKeyDown={onKey} className="flex flex-wrap justify-center gap-2">
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
                  className={`min-h-10 rounded-full border px-4 text-sm font-medium transition-colors duration-150 ${
                    on
                      ? "border-accent bg-accent-subtle text-accent"
                      : "border-line bg-surface text-muted hover:border-line-strong hover:text-ink"
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
            className="card mt-8 grid gap-6 p-4 sm:p-6 lg:grid-cols-[1.15fr_1fr]"
          >
            <div className="flex flex-col gap-4">
              <PhoneMessage ex={ex} />
              <p className="flex items-start gap-2.5 rounded-xl bg-success-subtle px-4 py-3 text-[0.9375rem] text-ink">
                <CircleCheck className="mt-0.5 size-5 shrink-0 text-success" aria-hidden="true" />
                <span>
                  <span className="font-medium">The right thing to do:</span> {ex.correct}.
                </span>
              </p>
            </div>
            <ul className="space-y-3" aria-label="What each defense did">
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
        </Reveal>
      </div>
    </section>
  );
}
