import { ShieldCheck } from "lucide-react";
import { GithubIcon } from "./GithubIcon";
import { REPO_URL } from "../data";

const LINKS = [
  { href: "#results", label: "Results" },
  { href: "#attacks", label: "Real attacks" },
  { href: "#how", label: "How it works" },
  { href: "#method", label: "Method" },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-bg/80 backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6" aria-label="Main">
        <a href="#top" className="flex items-center gap-2 font-semibold text-ink-strong">
          <ShieldCheck className="h-6 w-6 text-accent" aria-hidden="true" />
          Agent Shield
        </a>
        <div className="flex items-center gap-1 sm:gap-2">
          <ul className="hidden items-center gap-1 md:flex">
            {LINKS.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  className="rounded-md px-3 py-2 text-sm text-muted transition-colors hover:text-ink-strong"
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
          <a
            href={REPO_URL}
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-line px-3 text-sm text-ink transition-colors hover:border-accent/60 hover:text-ink-strong"
          >
            <GithubIcon className="h-4 w-4" aria-hidden="true" />
            <span>GitHub</span>
          </a>
        </div>
      </nav>
    </header>
  );
}
