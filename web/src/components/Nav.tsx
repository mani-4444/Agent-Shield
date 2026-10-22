import { ShieldCheck } from "lucide-react";
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
      className={`sticky top-0 z-40 border-b bg-bg/75 backdrop-blur-xl backdrop-saturate-150 transition-colors duration-200 ${
        scrolled ? "border-line" : "border-transparent"
      }`}
    >
      <nav className="wrapper flex h-14 items-center justify-between gap-4" aria-label="Main">
        <a href="#top" className="flex items-center gap-2.5 font-semibold tracking-tight text-ink">
          <ShieldCheck className="size-5" aria-hidden="true" />
          Agent Shield
        </a>
        <div className="flex items-center gap-1">
          <ul className="mr-2 hidden items-center gap-1 md:flex">
            {LINKS.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  className="rounded-lg px-3 py-2 text-sm text-muted transition-colors duration-150 hover:text-ink"
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
          <ThemeToggle />
          <a
            href={REPO_URL}
            className="inline-flex h-10 items-center gap-2 rounded-full px-3 text-sm text-muted transition-colors duration-150 hover:text-ink"
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
