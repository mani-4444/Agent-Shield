import { Comparison } from "./components/Comparison";
import { Examples } from "./components/Examples";
import { Footer } from "./components/Footer";
import { Heatmap } from "./components/Heatmap";
import { Hero } from "./components/Hero";
import { HowItWorks } from "./components/HowItWorks";
import { Methodology } from "./components/Methodology";
import { Nav } from "./components/Nav";
import { Stats } from "./components/Stats";

export default function App() {
  return (
    <>
      <a
        href="#results"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-bg"
      >
        Skip to results
      </a>
      <Nav />
      <main>
        <Hero />
        <Stats />
        <Comparison />
        <Heatmap />
        <Examples />
        <HowItWorks />
        <Methodology />
      </main>
      <Footer />
    </>
  );
}
