import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { DataBanner } from "./components/DataBanner";
import { Examples } from "./components/Examples";
import { Footer } from "./components/Footer";
import { Heatmap } from "./components/Heatmap";
import { Hero } from "./components/Hero";
import { HowItWorks } from "./components/HowItWorks";
import { KeyFigures } from "./components/KeyFigures";
import { Methodology } from "./components/Methodology";
import { Nav, type View } from "./components/Nav";
import { Results } from "./components/Results";
import { headline, results } from "./data";

// The trial browser and its data load only when someone opens #/trials.
const TrialsPage = lazy(() => import("./components/TrialsPage").then((m) => ({ default: m.TrialsPage })));

function viewOf(hash: string): View {
  return hash.startsWith("#/trials") ? "trials" : "home";
}

/** Hash routing: "#/trials" is the trial browser; any other hash is an anchor on the home page. */
function useView(): View {
  const [view, setView] = useState(() => viewOf(window.location.hash));
  useEffect(() => {
    const onHash = () => {
      const next = viewOf(window.location.hash);
      setView((prev) => {
        if (prev !== next && next === "trials") window.scrollTo({ top: 0, behavior: "instant" });
        return next;
      });
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  // Coming back from the trial browser to a home anchor: scroll once the section exists.
  useEffect(() => {
    if (view !== "home") return;
    const id = window.location.hash.slice(1);
    if (id) requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView());
  }, [view]);
  return view;
}

export default function App() {
  const view = useView();
  const names = useMemo(() => Object.fromEntries(headline(results).map((r) => [r.config, r.name])), []);
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-lg focus:bg-accent-solid focus:px-4 focus:py-2 focus:text-on-accent"
      >
        Skip to content
      </a>
      <Nav view={view} />
      <main id="main" tabIndex={-1}>
        {view === "trials" ? (
          <Suspense fallback={<p className="wrapper pt-20 text-muted">Loading the trial browser…</p>}>
            <TrialsPage names={names} />
          </Suspense>
        ) : (
          <>
            <Hero />
            <KeyFigures />
            <DataBanner />
            <Results />
            <Heatmap />
            <Examples />
            <HowItWorks />
            <Methodology />
          </>
        )}
      </main>
      <Footer />
    </>
  );
}
