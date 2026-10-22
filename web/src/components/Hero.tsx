import { ChevronRight, Database } from "lucide-react";
import { REPO_URL, headline, metric, per100, results } from "../data";
import { Enter } from "../motion";
import { Simulator } from "./Simulator";

export function Hero() {
  const rows = headline(results);
  const from = per100(metric(rows.find((r) => r.config === "a"), "asr_mean")?.value);
  const to = per100(metric(rows.find((r) => r.config === "d"), "asr_mean")?.value);

  return (
    <section id="top">
      <div className="wrapper pt-20 pb-20 text-center sm:pt-28 lg:pb-28">
        <Enter>
        <p className="text-lg font-medium text-muted sm:text-xl">
          Agent Shield · <span className="num">{results.n_records.toLocaleString("en-IN")}</span> trials, 5 defenses
        </p>

        </Enter>
        <Enter delay={0.08}>
        <h1 className="mx-auto mt-4 max-w-[16ch] text-display text-ink">
          Hidden text can trick an AI into paying a scammer.
        </h1>
        </Enter>
        <Enter delay={0.18}>
        <p className="mx-auto mt-6 max-w-[40rem] text-lg text-muted sm:text-xl">
          We attacked an AI payment assistant with booby-trapped bank texts, receipts and chats, and tested five
          defenses. The best one cut successful attacks from{" "}
          <span className="font-semibold whitespace-nowrap text-ink">
            {from} in 100 to {to}
          </span>
          .
        </p>

        </Enter>
        <Enter delay={0.28} className="mt-9 flex flex-wrap items-center justify-center gap-x-4 gap-y-4">
          <a
            href="#results"
            className="press inline-flex h-12 items-center rounded-full bg-accent-solid px-7 text-lg font-medium text-on-accent hover:bg-accent-solid-hover"
          >
            See the results
          </a>
          <a
            href="#/trials"
            className="press inline-flex h-12 items-center gap-2 rounded-full border border-accent/60 bg-accent-subtle px-6 text-lg font-medium text-accent hover:border-accent"
          >
            <Database className="size-5" aria-hidden="true" />
            Browse all {results.n_records.toLocaleString("en-IN")} trials
          </a>
          <a href={REPO_URL} className="group inline-flex min-h-12 items-center gap-0.5 px-2 text-lg text-accent">
            <span className="group-hover:underline">View the code</span>
            <ChevronRight className="size-5 transition-transform duration-200 group-hover:translate-x-0.5" aria-hidden="true" />
          </a>
        </Enter>

        <Enter delay={0.42} className="mx-auto mt-16 max-w-6xl sm:mt-20">
          <Simulator />
        </Enter>
      </div>
    </section>
  );
}
