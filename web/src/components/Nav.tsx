import { motion } from "framer-motion";
import { BookOpen, ChartColumn, Database, ShieldAlert, Workflow, type LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { REPO_URL } from "../data";
import { GithubIcon } from "./GithubIcon";
import { ThemeToggle } from "./ThemeToggle";

export type View = "home" | "trials";

const LINKS: { id: string; href: string; label: string; short: string; Icon: LucideIcon }[] = [
  { id: "results", href: "#results", label: "Results", short: "Results", Icon: ChartColumn },
  { id: "attacks", href: "#attacks", label: "Real attacks", short: "Attacks", Icon: ShieldAlert },
  { id: "trials", href: "#/trials", label: "All trials", short: "Trials", Icon: Database },
  { id: "how", href: "#how", label: "How it works", short: "How", Icon: Workflow },
  { id: "method", href: "#method", label: "Method", short: "Method", Icon: BookOpen },
];

/** The home section currently in the middle of the screen (null over the hero). */
function useActiveSection(enabled: boolean): string | null {
  const [active, setActive] = useState<string | null>(null);
  useEffect(() => {
    if (!enabled) return;
    const els = LINKS.map((l) => document.getElementById(l.id)).filter((el): el is HTMLElement => el != null);
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(e.target.id);
      },
      { rootMargin: "-45% 0px -50% 0px" },
    );
    els.forEach((el) => io.observe(el));
    const onTop = () => {
      if (window.scrollY < 300) setActive(null);
    };
    window.addEventListener("scroll", onTop, { passive: true });
    return () => {
      io.disconnect();
      window.removeEventListener("scroll", onTop);
    };
  }, [enabled]);
  return enabled ? active : null;
}

/**
 * Liquid-glass navigation: a floating capsule at the top (links on wide screens, with a glass
 * pill that slides to the current section) and, on phones, a floating tab bar at the bottom.
 */
export function Nav({ view }: { view: View }) {
  const section = useActiveSection(view === "home");
  const current = view === "trials" ? "trials" : section;

  return (
    <>
      <header className="sticky top-0 z-40 px-3 pt-3">
        <nav
          className="glass relative mx-auto flex h-14 max-w-[76rem] items-center justify-between gap-4 rounded-full pr-2 pl-4"
          aria-label="Main"
        >
          <a href="#top" className="flex items-center gap-2.5 font-serif text-lg font-medium text-ink">
            <img src={`${import.meta.env.BASE_URL}logo-128.png`} alt="" width={32} height={32} className="size-8" />
            Agent Shield
          </a>
          <ul className="hidden items-center md:flex">
            {LINKS.map((l) =>
              l.id === "trials" ? (
                <li key={l.id} className="mx-1.5">
                  <a
                    href={l.href}
                    aria-current={current === "trials" ? "page" : undefined}
                    className={`press inline-flex h-9 items-center gap-1.5 rounded-full bg-accent-solid px-4 text-sm font-medium text-on-accent hover:bg-accent-solid-hover ${
                      current === "trials" ? "ring-2 ring-accent/50 ring-offset-2 ring-offset-transparent" : ""
                    }`}
                  >
                    <Database className="size-4" aria-hidden="true" />
                    {l.label}
                  </a>
                </li>
              ) : (
              <li key={l.id}>
                <a
                  href={l.href}
                  aria-current={current === l.id ? (l.id === "trials" ? "page" : "true") : undefined}
                  className={`relative isolate block rounded-full px-3.5 py-2 text-sm transition-colors duration-200 ${
                    current === l.id ? "text-ink" : "text-muted hover:text-ink"
                  }`}
                >
                  {current === l.id && (
                    <motion.span
                      layoutId="nav-pill"
                      className="glass-pill absolute inset-0 -z-10 rounded-full"
                      transition={{ type: "spring", stiffness: 420, damping: 36 }}
                    />
                  )}
                  {l.label}
                </a>
              </li>
              ),
            )}
          </ul>
          <div className="flex items-center">
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

      <nav
        aria-label="Sections"
        className="glass fixed inset-x-3 bottom-[max(0.75rem,env(safe-area-inset-bottom))] z-40 grid grid-cols-5 rounded-[1.75rem] p-1.5 md:hidden"
      >
        {LINKS.map((l) => {
          const on = current === l.id;
          return (
            <a
              key={l.id}
              href={l.href}
              aria-current={on ? (l.id === "trials" ? "page" : "true") : undefined}
              className={`press relative isolate flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-[1.375rem] text-sm font-medium ${
                on ? "text-accent" : "text-muted"
              }`}
            >
              {on && (
                <motion.span
                  layoutId="tab-pill"
                  className="glass-pill absolute inset-0 -z-10 rounded-[1.375rem]"
                  transition={{ type: "spring", stiffness: 420, damping: 36 }}
                />
              )}
              {l.id === "trials" ? (
                <span className="grid size-7 place-items-center rounded-full bg-accent-solid text-on-accent" aria-hidden="true">
                  <l.Icon className="size-4" />
                </span>
              ) : (
                <l.Icon className="size-5" aria-hidden="true" />
              )}
              {l.short}
            </a>
          );
        })}
      </nav>
    </>
  );
}
