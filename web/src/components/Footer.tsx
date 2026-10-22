import { ShieldCheck } from "lucide-react";
import { GithubIcon } from "./GithubIcon";
import { REPO_URL, results } from "../data";

export function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 text-sm text-muted sm:flex-row sm:items-start sm:justify-between sm:px-6">
        <div className="max-w-xl space-y-2">
          <p className="flex items-center gap-2 font-semibold text-ink-strong">
            <ShieldCheck className="h-5 w-5 text-accent" aria-hidden="true" />
            Agent Shield
          </p>
          <p>
            Every number on this page comes from <code className="font-mono text-ink">results/{results.run_id}/summary.csv</code>{" "}
            ({results.n_records.toLocaleString("en-IN")} trials, model {results.model_ids.join(", ")}
            {results.run_date ? `, run ${results.run_date}` : ""}).
          </p>
          <p>
            All names, phone numbers, UPI IDs and accounts are made up. No real payments were made. Built with help from
            an AI coding assistant; design decisions and checks are the author's.
          </p>
        </div>
        <a
          href={REPO_URL}
          className="inline-flex min-h-11 items-center gap-2 self-start rounded-lg border border-line px-4 text-ink transition-colors hover:border-accent/60"
        >
          <GithubIcon className="h-4 w-4" aria-hidden="true" />
          Code, data and full report
        </a>
      </div>
    </footer>
  );
}
