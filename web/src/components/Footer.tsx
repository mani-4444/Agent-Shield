import { REPO_URL, results } from "../data";
import { GithubIcon } from "./GithubIcon";

export function Footer() {
  return (
    <footer className="border-t border-line bg-band">
      <div className="wrapper grid gap-8 pt-12 pb-32 text-sm text-muted md:grid-cols-[1fr_auto] md:pb-12">
        <div className="max-w-[44rem] space-y-3">
          <p className="flex items-center gap-2.5 font-serif text-lg font-medium text-ink">
            <img src={`${import.meta.env.BASE_URL}logo-128.png`} alt="" width={32} height={32} className="size-8" />
            Agent Shield
          </p>
          <p>
            Every number on this page comes from{" "}
            <code className="num rounded bg-surface-2 px-1.5 py-0.5 text-ink">results/{results.run_id}/summary.csv</code> (
            {results.n_records.toLocaleString("en-IN")} trials, model {results.model_ids.join(", ")}
            {results.run_date ? `, run ${results.run_date}` : ""}).
          </p>
          <p>
            All names, phone numbers, UPI IDs and accounts are made up. No real payments were made. Built with help from
            an AI coding assistant; the design decisions and checks are the author’s.
          </p>
        </div>
        <div>
          <a
            href={REPO_URL}
            className="inline-flex h-11 items-center gap-2 rounded-full border border-line px-5 font-medium text-ink transition-colors hover:border-line-strong"
          >
            <GithubIcon className="size-4" />
            Code, data and full report
          </a>
        </div>
      </div>
    </footer>
  );
}
