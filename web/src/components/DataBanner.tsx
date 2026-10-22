import { ArrowRight, ChevronRight, Database } from "lucide-react";
import { RELEASES_URL, headline, results } from "../data";
import { Reveal } from "../motion";

/** Points every visitor to the full data: the trial browser and the raw release. */
export function DataBanner() {
  const defenses = headline(results).length;
  const facts: [string, string][] = [
    [results.n_docs.toLocaleString("en-IN"), "test messages, each one open"],
    [results.n_records.toLocaleString("en-IN"), "trials with what the AI actually did"],
    [String(defenses * results.trials), `outcomes per message (${defenses} defenses × ${results.trials} tries)`],
  ];
  return (
    <section aria-labelledby="data-title" className="wrapper mt-4">
      <Reveal className="card card-hover border-accent/40 bg-accent-subtle p-6 sm:p-10">
        <div className="grid items-center gap-10 lg:grid-cols-[1.4fr_1fr]">
          <div>
            <p className="eyebrow inline-flex items-center gap-2">
              <Database className="size-4" aria-hidden="true" />
              Open data
            </p>
            <h2 id="data-title" className="mt-3 text-3xl text-ink">
              Every trial is here. Check it yourself.
            </h2>
            <p className="mt-4 max-w-[38rem] text-lg text-muted">
              Don’t take the charts on trust: open any of the {results.n_docs} test messages and see exactly what each
              defense did on every try, filtered however you like.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-x-4 gap-y-3">
              <a
                href="#/trials"
                className="press group inline-flex h-12 items-center gap-2 rounded-full bg-accent-solid px-7 text-lg font-medium text-on-accent hover:bg-accent-solid-hover"
              >
                Browse all trials
                <ArrowRight
                  className="size-5 transition-transform duration-200 group-hover:translate-x-0.5"
                  aria-hidden="true"
                />
              </a>
              <a href={RELEASES_URL} className="group inline-flex min-h-12 items-center gap-0.5 px-2 text-lg text-accent">
                <span className="group-hover:underline">Download raw data</span>
                <ChevronRight
                  className="size-5 transition-transform duration-200 group-hover:translate-x-0.5"
                  aria-hidden="true"
                />
              </a>
            </div>
          </div>
          <dl className="divide-y divide-line border-y border-line">
            {facts.map(([value, label]) => (
              <div key={label} className="grid grid-cols-[6.5rem_1fr] items-baseline gap-4 py-4">
                <dd className="num text-right text-4xl font-semibold text-ink">{value}</dd>
                <dt className="row-start-1 col-start-2 text-muted">{label}</dt>
              </div>
            ))}
          </dl>
        </div>
      </Reveal>
    </section>
  );
}
