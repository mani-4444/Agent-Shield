import { CONFIG_ORDER, groupRows, metric, results } from "../data";
import { Reveal } from "../motion";

const FAMILIES: [string, string][] = [
  ["F1_override", "Direct order to the AI"],
  ["F2_roleplay", "Fake system or admin message"],
  ["F3_hidden", "Text hidden from people"],
  ["F4_multilingual", "Telugu or mixed language"],
  ["F5_toolarg", "Fake tool call or corrected details"],
  ["F6_exfil", "Asks for the account number"],
];

/** Single-hue scale (attack red) from transparent to strong; values are always printed in the cell. */
function cellStyle(v: number | null) {
  if (v == null) return { background: "rgba(148,163,184,0.06)" };
  const a = 0.08 + Math.min(1, v / 0.5) * 0.72;
  return { background: `rgba(248, 113, 113, ${a.toFixed(2)})` };
}

export function Heatmap() {
  const rows = groupRows(results, "family");
  const names = Object.fromEntries(results.rows.filter((r) => r.group === "all").map((r) => [r.config, r.name]));

  return (
    <section aria-labelledby="where" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <Reveal>
        <h2 id="where" className="text-3xl font-bold tracking-tight text-ink-strong sm:text-4xl">
          Which tricks get through which defense
        </h2>
        <p className="mt-3 max-w-3xl text-muted">
          Attacks that worked, out of 100, for each kind of trick. Darker red means more attacks got through.
        </p>
        <p className="mt-2 text-xs text-muted md:hidden">Swipe the table sideways to see all five defenses.</p>
      </Reveal>
      <Reveal delay={0.1} className="mt-8 overflow-x-auto">
        <table className="w-full min-w-[720px] table-fixed border-separate border-spacing-1.5 text-sm">
          <thead>
            <tr>
              <th scope="col" className="w-52 px-2 text-left font-medium text-muted">Kind of trick</th>
              {CONFIG_ORDER.map((c) => (
                <th key={c} scope="col" className="px-2 pb-2 text-center text-xs font-medium text-muted">
                  <span className="mx-auto mb-1.5 block h-1 w-8 rounded-full" style={{ background: `var(--color-cfg-${c})` }} aria-hidden="true" />
                  {names[c] ?? c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {FAMILIES.map(([fam, label]) => (
              <tr key={fam}>
                <th scope="row" className="px-2 py-1 text-left font-medium text-ink">{label}</th>
                {CONFIG_ORDER.map((c) => {
                  const m = metric(rows.find((r) => r.config === c && r.group === `family=${fam}`), "asr_mean");
                  const v = m?.value ?? null;
                  return (
                    <td key={c} className="h-14 rounded-lg text-center font-mono text-ink-strong" style={cellStyle(v)}>
                      {v == null ? "–" : Math.floor(v * 100 + 0.5)}
                      {m && m.n_docs < 30 && <span className="block text-[10px] font-sans text-ink/70">few messages</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>
      <Reveal delay={0.15}>
        <ul className="mt-8 grid gap-3 text-sm sm:grid-cols-2">
          <li className="rounded-xl border border-line bg-surface p-4">
            <span className="font-semibold text-ink-strong">The fact-checker stops almost everything</span>
            <span className="block text-muted">because the AI never gets the power to pay or see private details.</span>
          </li>
          <li className="rounded-xl border border-line bg-surface p-4">
            <span className="font-semibold text-ink-strong">Its weak spot is fake "corrected" details</span>
            <span className="block text-muted">a believable new amount or payee still passes the fact check sometimes.</span>
          </li>
          <li className="rounded-xl border border-line bg-surface p-4">
            <span className="font-semibold text-ink-strong">The attack detector catches loud tricks</span>
            <span className="block text-muted">like "ignore your rules", but misses quiet ones such as requests for the account number.</span>
          </li>
          <li className="rounded-xl border border-line bg-surface p-4">
            <span className="font-semibold text-ink-strong">A warning label is not enough</span>
            <span className="block text-muted">telling the AI to ignore instructions helps only a little.</span>
          </li>
        </ul>
      </Reveal>
    </section>
  );
}
