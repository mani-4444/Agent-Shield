import { Check, ChevronDown, Download, Minus, Search, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { CONFIG_ORDER, RELEASES_URL, loadTrials, results, shortName } from "../data";
import { Reveal } from "../motion";
import type { ConfigId, Trial, TrialDoc } from "../types";
import { ChoiceGroup } from "./ChoiceGroup";
import { Highlighted } from "./Highlighted";

const PAGE = 25;
const DOC_TYPES: Record<TrialDoc["doc_type"], string> = {
  bank_sms: "Bank SMS",
  receipt_ocr: "Scanned receipt",
  chat_message: "Chat message",
};
const LANGS: Record<TrialDoc["lang"], string> = { en: "English", te: "Telugu", "te-en": "Telugu-English mix" };

type Kind = "all" | "attack" | "normal";
type Outcome = "any" | "fooled" | "held" | "wrong";

function outcomeOf(t: Trial): "fooled" | "right" | "wrong" {
  return t.attack_worked ? "fooled" : t.correct ? "right" : "wrong";
}

const MARK = {
  fooled: { Icon: X, cls: "bg-danger text-on-strong", label: "Attack worked" },
  right: { Icon: Check, cls: "bg-success-subtle text-success", label: "Right call" },
  wrong: { Icon: Minus, cls: "bg-surface-2 text-muted", label: "Not fooled, but a different decision" },
} as const;

/** One trial as a small icon mark; the icon and a text label carry the meaning, not colour. */
function Mark({ t, n }: { t: Trial; n: number }) {
  const m = MARK[outcomeOf(t)];
  return (
    <span className={`grid size-6 place-items-center rounded-md ${m.cls}`} title={`Try ${n}: ${m.label}`}>
      <m.Icon className="size-3.5" strokeWidth={3} aria-hidden="true" />
      <span className="sr-only">
        Try {n}: {m.label}.
      </span>
    </span>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex min-w-0 flex-col gap-1.5 text-sm text-muted">
      {label}
      {children}
    </label>
  );
}

const control =
  "h-10 w-full min-w-0 rounded-full border border-line bg-surface px-4 text-sm text-ink transition-colors hover:border-line-strong";

export function TrialsPage({ names }: { names: Record<string, string> }) {
  const [docs, setDocs] = useState<TrialDoc[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<Kind>("all");
  const [family, setFamily] = useState("");
  const [lang, setLang] = useState("");
  const [focus, setFocus] = useState<ConfigId>("d");
  const [outcome, setOutcome] = useState<Outcome>("any");
  const [shown, setShown] = useState(PAGE);
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    heading.current?.focus();
    loadTrials().then(setDocs, () => setFailed(true));
  }, []);

  const families = useMemo(() => {
    const seen = new Map<string, string>();
    for (const d of docs ?? []) if (d.family && d.family_name) seen.set(d.family, d.family_name);
    return [...seen].sort();
  }, [docs]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (docs ?? []).filter((d) => {
      if (kind === "attack" && !d.family) return false;
      if (kind === "normal" && d.family) return false;
      if (family && d.family !== family) return false;
      if (lang && d.lang !== lang) return false;
      if (q && !d.doc_id.toLowerCase().includes(q) && !d.message.toLowerCase().includes(q)) return false;
      const ts = d.trials[focus] ?? [];
      if (outcome === "fooled") return ts.some((t) => t.attack_worked);
      if (outcome === "held") return d.family != null && ts.length > 0 && ts.every((t) => !t.attack_worked);
      if (outcome === "wrong") return ts.some((t) => !t.correct);
      return true;
    });
  }, [docs, query, kind, family, lang, focus, outcome]);

  useEffect(() => setShown(PAGE), [query, kind, family, lang, focus, outcome]);

  // Tally over the filtered messages, counted in tries.
  const tally = useMemo(
    () =>
      CONFIG_ORDER.map((c) => {
        let worked = 0, attackTries = 0, right = 0, tries = 0; // prettier-ignore
        for (const d of filtered)
          for (const t of d.trials[c] ?? []) {
            tries++;
            if (t.correct) right++;
            if (t.attack_worked != null) {
              attackTries++;
              if (t.attack_worked) worked++;
            }
          }
        return { c, worked, attackTries, right, tries };
      }),
    [filtered],
  );

  function reset() {
    setQuery("");
    setKind("all");
    setFamily("");
    setLang("");
    setOutcome("any");
  }

  return (
    <div className="wrapper pt-14 pb-24 sm:pt-20">
      <Reveal className="max-w-[46rem]">
        <p className="eyebrow">All trials</p>
        <h1 ref={heading} tabIndex={-1} className="mt-3 text-3xl text-ink outline-none">
          Every message, every defense, every try
        </h1>
        <p className="mt-5 text-lg text-muted">
          All {results.n_docs} test messages and all {results.n_records.toLocaleString("en-IN")} trials from the run,
          scored by the same rules as the headline numbers. Filter them, open any message, and see what each defense did
          on each of its {results.trials} tries.
        </p>
        <a href={RELEASES_URL} className="group mt-5 inline-flex min-h-11 items-center gap-2 text-accent">
          <Download className="size-4" aria-hidden="true" />
          <span className="group-hover:underline">Raw records for researchers (GitHub Releases)</span>
        </a>
      </Reveal>

      <section aria-label="Filters" className="card mt-10 grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Search text or message ID">
          <span className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2" aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. fakepay or t-167"
              className={`${control} pl-10`}
            />
          </span>
        </Field>
        <Field label="Kind of trick">
          <select value={family} onChange={(e) => setFamily(e.target.value)} className={control}>
            <option value="">Any</option>
            {families.map(([f, n]) => (
              <option key={f} value={f}>
                {n}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Language">
          <select value={lang} onChange={(e) => setLang(e.target.value)} className={control}>
            <option value="">Any</option>
            {Object.entries(LANGS).map(([v, n]) => (
              <option key={v} value={v}>
                {n}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Only where this defense…">
          <span className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            <select
              aria-label="Defense"
              value={focus}
              onChange={(e) => setFocus(e.target.value as ConfigId)}
              className={control}
            >
              {CONFIG_ORDER.map((c) => (
                <option key={c} value={c}>
                  {shortName(names[c] ?? c)}
                </option>
              ))}
            </select>
            <select
              aria-label="Outcome"
              value={outcome}
              onChange={(e) => setOutcome(e.target.value as Outcome)}
              className={control}
            >
              <option value="any">any result</option>
              <option value="fooled">was fooled</option>
              <option value="held">always held</option>
              <option value="wrong">made a mistake</option>
            </select>
          </span>
        </Field>
        <div className="flex flex-wrap items-center justify-between gap-3 sm:col-span-2 lg:col-span-4">
          <ChoiceGroup
            id="trial-kind"
            label="Messages"
            value={kind}
            onChange={setKind}
            options={[
              { value: "all", label: "All messages" },
              { value: "attack", label: "With an attack" },
              { value: "normal", label: "Normal" },
            ]}
          />
          <button type="button" onClick={reset} className="press min-h-10 rounded-full px-4 text-sm text-accent hover:underline">
            Clear filters
          </button>
        </div>
      </section>

      {failed && <p className="mt-10 text-danger">The trial data could not be loaded. Please reload the page.</p>}
      {!docs && !failed && (
        <p className="mt-10 text-muted" role="status">
          Loading {results.n_records.toLocaleString("en-IN")} trials…
        </p>
      )}

      {docs && (
        <>
          <div className="card mt-4 overflow-x-auto p-5" role="region" aria-label="Tally for the filtered messages" tabIndex={0}>
            <p className="text-sm text-muted" role="status">
              Showing <span className="num font-semibold text-ink">{filtered.length}</span> of {docs.length} messages.
              Counts below are tries, across all of them.
            </p>
            <table className="mt-3 w-full min-w-[34rem] text-left text-sm">
              <thead className="text-muted">
                <tr>
                  <th scope="col" className="py-2 font-medium">
                    Defense
                  </th>
                  <th scope="col" className="py-2 font-medium">
                    Attacks that worked
                  </th>
                  <th scope="col" className="py-2 font-medium">
                    Right call
                  </th>
                </tr>
              </thead>
              <tbody>
                {tally.map(({ c, worked, attackTries, right, tries }) => (
                  <tr key={c} className="border-t border-line">
                    <th scope="row" className={`py-2 font-normal ${c === "d" ? "text-accent" : "text-ink"}`}>
                      {names[c] ?? c}
                    </th>
                    <td className="num py-2 text-ink">
                      {attackTries ? `${worked} of ${attackTries}` : "–"}
                      {attackTries > 0 && (
                        <span className="text-muted"> ({Math.round((100 * worked) / attackTries)}%)</span>
                      )}
                    </td>
                    <td className="num py-2 text-ink">
                      {tries ? `${right} of ${tries}` : "–"}
                      {tries > 0 && <span className="text-muted"> ({Math.round((100 * right) / tries)}%)</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-muted" aria-label="Legend">
            {Object.values(MARK).map((m) => (
              <li key={m.label} className="flex items-center gap-2">
                <span className={`grid size-5 place-items-center rounded-md ${m.cls}`} aria-hidden="true">
                  <m.Icon className="size-3" strokeWidth={3} />
                </span>
                {m.label}
              </li>
            ))}
          </ul>

          <ul className="mt-6 space-y-3">
            {filtered.slice(0, shown).map((d) => (
              <TrialCard key={d.doc_id} d={d} names={names} onOpenTwin={(id) => {
                  reset();
                  setQuery(id);
                }} />
            ))}
          </ul>

          {filtered.length === 0 && (
            <p className="mt-10 text-muted">
              No messages match these filters.{" "}
              <button type="button" onClick={reset} className="text-accent hover:underline">
                Clear filters
              </button>
            </p>
          )}
          {shown < filtered.length && (
            <div className="mt-8 text-center">
              <button
                type="button"
                onClick={() => setShown((s) => s + PAGE)}
                className="press inline-flex h-12 items-center rounded-full border border-line px-6 font-medium text-ink hover:border-line-strong"
              >
                Show {Math.min(PAGE, filtered.length - shown)} more
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function TrialCard({ d, names, onOpenTwin }: { d: TrialDoc; names: Record<string, string>; onOpenTwin: (id: string) => void }) {
  const [open, setOpen] = useState(false);
  const panel = `trial-${d.doc_id}`;
  return (
    <li className="card card-hover overflow-hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panel}
        onClick={() => setOpen((o) => !o)}
        className="grid w-full gap-4 p-4 text-left sm:p-5 lg:grid-cols-[1fr_auto]"
      >
        <span className="min-w-0">
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted">
            <span className="num text-ink">{d.doc_id}</span>
            <span>{DOC_TYPES[d.doc_type]}</span>
            <span>{LANGS[d.lang]}</span>
            {d.family_name ? (
              <span className="rounded-full bg-danger-subtle px-2.5 py-0.5 text-danger">{d.family_name}</span>
            ) : (
              <span className="rounded-full bg-surface-2 px-2.5 py-0.5">Normal message</span>
            )}
          </span>
          <span className="mt-2 line-clamp-2 block text-[0.9375rem] text-ink" lang={d.lang === "te" ? "te" : "en"}>
            {d.message}
          </span>
        </span>
        <span className="flex items-center gap-4">
          <span className="grid grid-cols-[auto_repeat(3,1.5rem)] items-center gap-x-1.5 gap-y-1">
            {CONFIG_ORDER.map((c) => (
              <span key={c} className="contents">
                <span className="pr-1.5 text-right text-sm text-muted">{shortName(names[c] ?? c)}</span>
                {(d.trials[c] ?? []).map((t, i) => (
                  <Mark key={i} t={t} n={i + 1} />
                ))}
              </span>
            ))}
          </span>
          <ChevronDown
            className={`size-5 shrink-0 text-muted transition-transform duration-300 ${open ? "rotate-180" : ""}`}
            aria-hidden="true"
          />
        </span>
      </button>

      {open && (
        <div id={panel} className="grid gap-6 border-t border-line p-4 sm:p-5 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <p className="text-sm font-medium text-muted">The message the assistant read</p>
            <p
              className="mt-2 rounded-2xl bg-surface-2 px-4 py-3 text-[0.9375rem] leading-relaxed break-words whitespace-pre-wrap text-ink"
              lang={d.lang === "te" ? "te" : "en"}
            >
              <Highlighted message={d.message} hidden={d.hidden_instruction ?? ""} />
            </p>
            {d.hidden_from_humans && <p className="mt-2 text-sm text-danger">The marked text is invisible to a person.</p>}
            <p className="mt-3 text-sm text-muted">
              Right action: <span className="text-ink">{d.correct}</span>.
            </p>
            {d.goal_name && (
              <p className="mt-1 text-sm text-muted">
                Attacker’s goal: <span className="text-ink">{d.goal_name.toLowerCase()}</span>.
              </p>
            )}
            {d.twin_id && (
              <button type="button" onClick={() => onOpenTwin(d.twin_id ?? "")} className="mt-3 text-sm text-accent hover:underline">
                Compare with the same message without the attack ({d.twin_id})
              </button>
            )}
          </div>
          <table className="w-full text-left text-sm">
            <caption className="sr-only">What each defense did on each try</caption>
            <thead className="text-muted">
              <tr>
                <th scope="col" className="pb-2 font-medium">
                  Defense
                </th>
                <th scope="col" className="pb-2 font-medium">
                  What it did, per try
                </th>
              </tr>
            </thead>
            <tbody>
              {CONFIG_ORDER.map((c) => (
                <tr key={c} className="border-t border-line align-top">
                  <th scope="row" className="py-2 pr-3 font-medium text-ink">
                    {names[c] ?? c}
                  </th>
                  <td className="py-2">
                    <ol className="space-y-1.5">
                      {(d.trials[c] ?? []).map((t, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <Mark t={t} n={i + 1} />
                          <span className="text-muted">{t.text}</span>
                        </li>
                      ))}
                    </ol>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </li>
  );
}

