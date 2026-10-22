// Fails (exit 1) if any token pair in src/index.css misses WCAG 2.2 AA in either theme:
// text >= 4.5:1, UI parts (borders, focus ring, bars) >= 3:1. Run by `npm run build`.
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/index.css", import.meta.url), "utf8");

function block(selector) {
  const start = css.indexOf(`${selector} {`);
  if (start < 0) throw new Error(`no block ${selector}`);
  const body = css.slice(start, css.indexOf("}", start));
  const tokens = {};
  for (const m of body.matchAll(/--([\w-]+):\s*oklch\(([\d.]+)%\s+([\d.]+)\s+([\d.]+)\)/g)) {
    tokens[m[1]] = [Number(m[2]) / 100, Number(m[3]), Number(m[4])];
  }
  return tokens;
}

function luminance([L, C, h]) {
  const a = C * Math.cos((h * Math.PI) / 180);
  const b = C * Math.sin((h * Math.PI) / 180);
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const clip = (v) => Math.min(1, Math.max(0, v));
  const R = clip(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s);
  const G = clip(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s);
  const B = clip(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s);
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

const ratio = (x, y) => {
  const [a, b] = [luminance(x), luminance(y)].sort((p, q) => q - p);
  return (a + 0.05) / (b + 0.05);
};

const TEXT = [
  ["text", "bg"], ["text", "surface"], ["text", "bg-band"],
  ["text-muted", "bg"], ["text-muted", "surface"], ["text-muted", "bg-band"],
  ["accent", "bg"], ["accent", "surface"], ["accent", "bg-band"], ["accent", "accent-subtle"],
  ["on-accent", "accent"], ["text", "accent-subtle"],
  ["danger", "surface"], ["danger", "danger-subtle"], ["text", "danger-subtle"],
  ["success", "surface"], ["success", "success-subtle"], ["text", "success-subtle"],
  ["on-strong", "danger"],
];
const UI = [
  ["border-strong", "bg"], ["border-strong", "surface"],
  ["accent", "bg"], ["accent", "surface"],
  ["bar", "track"], ["bar", "surface"], ["bar", "bg-band"],
];

let failed = 0;
for (const [theme, selector] of [["light", ":root"], ["dark", ':root[data-theme="dark"]']]) {
  const t = block(selector);
  for (const [pairs, min] of [[TEXT, 4.5], [UI, 3]]) {
    for (const [fg, bg] of pairs) {
      const r = ratio(t[fg], t[bg]);
      const ok = r >= min;
      if (!ok) failed++;
      console.log(`${ok ? "ok  " : "FAIL"} ${theme.padEnd(5)} ${fg} on ${bg}: ${r.toFixed(2)} (min ${min})`);
    }
  }
}
if (failed) {
  console.error(`${failed} contrast pair(s) below WCAG AA`);
  process.exit(1);
}
