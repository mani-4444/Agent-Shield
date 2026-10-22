import { ShieldCheck } from "lucide-react";
import { REPO_URL, results } from "../data";
import { GithubIcon } from "./GithubIcon";

export function Footer() {
  return (
    <footer className="border-t border-line bg-band">
      <div className="wrapper grid gap-8 py-12 text-sm text-muted md:grid-cols-[1fr_auto]">
        <div className="max-w-[44rem] space-y-3">
          <p className="flex items-center gap-2.5 text-base font-semibold text-ink">
            <ShieldCheck className="size-5" aria-hidden="true" />
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
