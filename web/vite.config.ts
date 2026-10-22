import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Served from https://mani-4444.github.io/Agent-Shield/ (GitHub Pages project site).
export default defineConfig({
  base: "/Agent-Shield/",
  plugins: [react(), tailwindcss()],
});
