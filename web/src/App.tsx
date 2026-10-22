import { Examples } from "./components/Examples";
import { Footer } from "./components/Footer";
import { Heatmap } from "./components/Heatmap";
import { Hero } from "./components/Hero";
import { HowItWorks } from "./components/HowItWorks";
import { KeyFigures } from "./components/KeyFigures";
import { Methodology } from "./components/Methodology";
import { Nav } from "./components/Nav";
import { Results } from "./components/Results";

export default function App() {
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-[var(--radius-control)] focus:bg-accent focus:px-4 focus:py-2 focus:text-on-accent"
      >
        Skip to content
      </a>
      <Nav />
      <main id="main" tabIndex={-1}>
        <Hero />
        <KeyFigures />
        <Results />
        <Heatmap />
        <Examples />
        <HowItWorks />
        <Methodology />
      </main>
      <Footer />
    </>
  );
}
