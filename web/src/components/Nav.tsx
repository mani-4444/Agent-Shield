import { useEffect, useState } from "react";
import { REPO_URL } from "../data";
import { GithubIcon } from "./GithubIcon";
import { ThemeToggle } from "./ThemeToggle";

const LINKS = [
  { href: "#results", label: "Results" },
  { href: "#attacks", label: "Real attacks" },
  { href: "#how", label: "How it works" },
  { href: "#method", label: "Method" },
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-40 bg-bg transition-[border-color] duration-200 ${
        scrolled ? "shadow-header border-b border-line" : "border-b border-transparent"
      }`}
    >
      <nav className="wrapper flex h-16 items-center justify-between gap-4" aria-label="Main">
        <a href="#top" className="font-serif text-step-1 font-semibold tracking-tight text-ink">
          Agent Shield
        </a>
        <div className="flex items-center gap-1">
          <ul className="mr-2 hidden items-center gap-1 md:flex">
            {LINKS.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  className="rounded-[var(--radius-control)] px-3 py-2 text-step--1 text-muted transition-colors duration-150 hover:text-ink"
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
          <ThemeToggle />
          <a
            href={REPO_URL}
            className="inline-flex h-10 items-center gap-2 rounded-[var(--radius-control)] px-3 text-step--1 text-muted transition-colors duration-150 hover:bg-band hover:text-ink"
          >
            <GithubIcon className="size-4" />
            <span className="hidden sm:inline">GitHub</span>
            <span className="sr-only sm:hidden">GitHub repository</span>
          </a>
        </div>
      </nav>
    </header>
  );
}
