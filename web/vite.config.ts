import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Served from https://mani-4444.github.io/Agent-Shield/ (GitHub Pages project site).
export default defineConfig({
  base: "/Agent-Shield/",
  plugins: [react(), tailwindcss()],
  // trials.json (every trial, ~0.8 MB raw, ~45 KB gzipped) is its own lazy chunk, loaded only by
  // the trial browser; it is data, not code, so the 500 KB code-chunk warning does not apply.
  build: { chunkSizeWarningLimit: 900 },
});
