import { ChevronRight } from "lucide-react";
import { REPO_URL, headline, metric, per100, results } from "../data";
import { Simulator } from "./Simulator";

export function Hero() {
  const rows = headline(results);
  const from = per100(metric(rows.find((r) => r.config === "a"), "asr_mean")?.value);
  const to = per100(metric(rows.find((r) => r.config === "d"), "asr_mean")?.value);

  return (
    <section id="top">
      <div className="wrapper pt-20 pb-20 text-center sm:pt-28 lg:pb-28">
        <p className="text-lg font-medium text-muted sm:text-xl">
          Agent Shield · <span className="num">{results.n_records.toLocaleString("en-IN")}</span> trials, 5 defenses
        </p>

        <h1 className="mx-auto mt-4 max-w-[16ch] text-display text-ink">
          Hidden text can trick an AI into paying a scammer.
        </h1>
        <p className="mx-auto mt-6 max-w-[40rem] text-lg text-muted sm:text-xl">
          We attacked an AI payment assistant with booby-trapped bank texts, receipts and chats, and tested five
          defenses. The best one cut successful attacks from{" "}
          <span className="font-semibold whitespace-nowrap text-ink">
            {from} in 100 to {to}
          </span>
          .
        </p>

        <div className="mt-9 flex flex-wrap items-center justify-center gap-x-8 gap-y-4">
          <a
            href="#results"
            className="inline-flex h-12 items-center rounded-full bg-accent-solid px-7 text-lg font-medium text-on-accent transition-colors duration-150 hover:bg-accent-solid-hover"
          >
            See the results
          </a>
          <a href={REPO_URL} className="group inline-flex min-h-12 items-center gap-0.5 text-lg text-accent">
            <span className="group-hover:underline">View the code</span>
            <ChevronRight className="size-5" aria-hidden="true" />
          </a>
        </div>

        <div className="mx-auto mt-16 max-w-6xl sm:mt-20">
          <Simulator />
        </div>
      </div>
    </section>
  );
}
