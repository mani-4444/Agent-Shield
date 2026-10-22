import { ArrowRight } from "lucide-react";
import { REPO_URL, headline, metric, per100, results } from "../data";
import { GithubIcon } from "./GithubIcon";
import { Simulator } from "./Simulator";

export function Hero() {
  const rows = headline(results);
  const from = per100(metric(rows.find((r) => r.config === "a"), "asr_mean")?.value);
  const to = per100(metric(rows.find((r) => r.config === "d"), "asr_mean")?.value);

  return (
    <section id="top" className="relative isolate overflow-hidden">
      <div className="dot-grid absolute inset-x-0 top-0 -z-10 h-[44rem]" aria-hidden="true" />
      <div className="spotlight absolute top-[26rem] left-1/2 -z-10 h-[28rem] w-[min(60rem,100%)] -translate-x-1/2" aria-hidden="true" />

      <div className="wrapper pt-16 pb-20 text-center sm:pt-24 lg:pb-28">
        <a
          href="#results"
          className="inline-flex min-h-9 items-center gap-2 rounded-full border border-line bg-surface/70 px-4 text-sm text-muted backdrop-blur transition-colors hover:border-line-strong hover:text-ink"
        >
          <span className="size-1.5 rounded-full bg-accent" aria-hidden="true" />
          <span className="num">{results.n_records.toLocaleString("en-IN")}</span> trials · 5 defenses · open data
          <ArrowRight className="size-3.5" aria-hidden="true" />
        </a>

        <h1 className="mx-auto mt-7 max-w-[17ch] text-display text-ink">
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

        <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
          <a
            href="#results"
            className="inline-flex h-12 items-center gap-2 rounded-xl bg-accent-solid px-6 font-medium text-on-accent shadow-[inset_0_1px_0_oklch(100%_0_0/0.2)] transition-colors duration-150 hover:bg-accent-solid-hover"
          >
            See the results
            <ArrowRight className="size-4" aria-hidden="true" />
          </a>
          <a
            href={REPO_URL}
            className="inline-flex h-12 items-center gap-2 rounded-xl border border-line bg-surface px-6 font-medium text-ink transition-colors duration-150 hover:border-line-strong"
          >
            <GithubIcon className="size-4" />
            View on GitHub
          </a>
        </div>

        <div className="mx-auto mt-16 max-w-6xl sm:mt-20">
          <Simulator />
        </div>
      </div>
    </section>
  );
}
