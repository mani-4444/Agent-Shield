import { REPO_URL, results } from "../data";
import { GithubIcon } from "./GithubIcon";

export function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="wrapper grid gap-8 py-12 text-step--1 text-muted md:grid-cols-12">
        <div className="space-y-3 md:col-span-8">
          <p className="font-serif text-step-1 text-ink">Agent Shield</p>
          <p className="prose">
            Every number on this page comes from{" "}
            <code className="font-mono text-ink">results/{results.run_id}/summary.csv</code> (
            {results.n_records.toLocaleString("en-IN")} trials, model {results.model_ids.join(", ")}
            {results.run_date ? `, run ${results.run_date}` : ""}).
          </p>
          <p className="prose">
            All names, phone numbers, UPI IDs and accounts are made up. No real payments were made. Built with help from
            an AI coding assistant; the design decisions and checks are the author’s.
          </p>
        </div>
        <div className="md:col-span-4 md:justify-self-end">
          <a href={REPO_URL} className="link inline-flex min-h-11 items-center gap-2">
            <GithubIcon className="size-4" aria-hidden="true" />
            Code, data and full report
          </a>
        </div>
      </div>
    </footer>
  );
}
