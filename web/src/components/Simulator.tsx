import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight, CircleCheck, CircleX } from "lucide-react";
import { useState } from "react";
import { examples, headline, metric, per100, results } from "../data";
import { EASE_OUT } from "../motion";
import type { ConfigId } from "../types";
import { ChoiceGroup } from "./ChoiceGroup";
import { PhoneMessage } from "./PhoneMessage";

/** Pick a trick and a defense; shows what that defense really did with that message in the run. */
export function Simulator() {
  const reduce = useReducedMotion();
  const rows = headline(results);
  const [family, setFamily] = useState(examples[0]?.family ?? "");
  const [config, setConfig] = useState<ConfigId>("a");
  const ex = examples.find((e) => e.family === family) ?? examples[0];
  if (!ex) return null;
  const act = ex.actions[config];
  const name = rows.find((r) => r.config === config)?.name ?? config;
  const checker = rows.find((r) => r.config === "d");

  return (
    <div className="card overflow-hidden text-left">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
        <p className="text-sm font-medium text-ink">Attack simulator</p>
        <p className="text-sm text-muted">Real messages and real outcomes from the test run</p>
      </div>

      <div className="grid lg:grid-cols-[1.2fr_1fr]">
        <div className="flex flex-col gap-4 p-5">
          <p id="sim-trick" className="text-sm font-medium text-muted">
            <span className="num mr-2 text-accent">01</span>Pick a trick
          </p>
          <ChoiceGroup
            id="sim-trick"
            label="Kind of trick"
            variant="chips"
            value={ex.family}
            onChange={setFamily}
            options={examples.map((e) => ({ value: e.family, label: e.family_name }))}
          />
          <div className="flex-1">
            <PhoneMessage ex={ex} />
          </div>
        </div>

        <div className="flex flex-col gap-4 border-t border-line bg-band p-5 lg:border-t-0 lg:border-l">
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-sm font-medium text-muted">
              <span className="num mr-2 text-accent">02</span>Pick a defense
            </p>
            <p className="text-sm text-muted">attacks through, per 100</p>
          </div>
          <ChoiceGroup
            id="sim-defense"
            label="Defense"
            variant="list"
            value={config}
            onChange={setConfig}
            options={rows.map((r) => ({
              value: r.config,
              label: (
                <span className="flex items-center justify-between gap-3">
                  <span>{r.name}</span>
                  <span className="num text-sm text-muted">{per100(metric(r, "asr_mean")?.value)}</span>
                </span>
              ),
            }))}
          />

          <div aria-live="polite" className="mt-auto">
            <AnimatePresence mode="wait" initial={false}>
              {act && (
                <motion.div
                  key={`${ex.family}-${config}`}
                  initial={reduce ? false : { opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={reduce ? undefined : { opacity: 0, y: -6 }}
                  transition={{ duration: 0.22, ease: EASE_OUT }}
                  className={`rounded-xl border p-4 ${
                    act.attack_succeeded ? "border-danger/40 bg-danger-subtle" : "border-success/40 bg-success-subtle"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {act.attack_succeeded ? (
                      <CircleX className="size-7 shrink-0 text-danger" aria-hidden="true" />
                    ) : (
                      <CircleCheck className="size-7 shrink-0 text-success" aria-hidden="true" />
                    )}
                    <p className="text-xl font-semibold tracking-tight text-ink">
                      {name}{" "}
                      <span className={act.attack_succeeded ? "text-danger" : "text-success"}>
                        {act.attack_succeeded ? "was fooled" : "held"}
                      </span>
                    </p>
                  </div>
                  <p className="mt-2 text-[0.9375rem] text-ink">{act.text}</p>
                  <p className="mt-1 text-sm text-muted">Correct action: {ex.correct}.</p>
                </motion.div>
              )}
            </AnimatePresence>
            {config !== "d" && act?.attack_succeeded && checker && (
              <button
                type="button"
                onClick={() => setConfig("d")}
                className="mt-3 inline-flex min-h-10 items-center gap-1.5 text-sm font-medium text-accent hover:underline"
              >
                See what the {checker.name.toLowerCase()} does
                <ArrowRight className="size-4" aria-hidden="true" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
