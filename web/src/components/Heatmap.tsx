import { CONFIG_ORDER, groupRows, headline, metric, results } from "../data";

const FAMILIES: [string, string][] = [
  ["F1_override", "Direct order to the AI"],
  ["F2_roleplay", "Fake system or admin message"],
  ["F3_hidden", "Text hidden from people"],
  ["F4_multilingual", "Telugu or mixed language"],
  ["F5_toolarg", "Fake tool call or corrected details"],
  ["F6_exfil", "Asks for the account number"],
];

const FINDINGS = [
  ["The fact-checker stops almost everything,", "because the AI never gets the power to pay or to see private details."],
  ["Its weak spot is fake “corrected” details.", "A believable new amount or payee still passes the fact check sometimes."],
  ["The attack detector catches loud tricks", "like “ignore your rules”, but misses quiet ones such as asking for the account number."],
  ["A warning label is not enough.", "Telling the AI to ignore instructions in the message helps only a little."],
];

/** One hue (danger), mixed into the surface; 0 is plain surface, 50+ in 100 is the strongest step. */
function cellStyle(v: number | null) {
  if (v == null) return {};
  const p = Math.round(Math.min(1, v / 0.5) * 70);
  return {
    background: `color-mix(in oklch, var(--danger) ${p}%, var(--surface))`,
    color: p >= 40 ? "var(--on-strong)" : "var(--text)",
  };
}

export function Heatmap() {
  const rows = groupRows(results, "family");
  const names = Object.fromEntries(headline(results).map((r) => [r.config, r.name]));

  return (
    <section aria-labelledby="where-title" className="section wrapper">
      <p className="eyebrow">Where defenses fail</p>
      <h2 id="where-title" className="mt-3 max-w-[22ch] text-step-4 text-ink">
        Which tricks get through which defense
      </h2>

      <div className="mt-10 grid gap-12 lg:grid-cols-12 lg:gap-16">
        <div className="min-w-0 lg:col-span-8">
          <p className="text-step--1 text-muted">
            Attacks that worked, out of 100, for each kind of trick. The stronger the red, the more got through.
            <span className="md:hidden"> Scroll the table sideways to see all five defenses.</span>
          </p>
          <div className="mt-4 overflow-x-auto" tabIndex={0} role="region" aria-labelledby="where-title">
            <table className="w-full min-w-[40rem] table-fixed border-collapse text-step--1">
              <thead>
                <tr className="border-b border-line-strong">
                  <th scope="col" className="w-[30%] py-3 pr-3 text-left font-medium text-muted">
                    Kind of trick
                  </th>
                  {CONFIG_ORDER.map((c) => (
                    <th key={c} scope="col" className="px-1 py-3 text-center align-bottom font-medium text-muted">
                      {names[c] ?? c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FAMILIES.map(([fam, label]) => (
                  <tr key={fam} className="border-b border-line">
                    <th scope="row" className="py-1 pr-3 text-left font-normal text-ink">
                      {label}
                    </th>
                    {CONFIG_ORDER.map((c) => {
                      const m = metric(rows.find((r) => r.config === c && r.group === `family=${fam}`), "asr_mean");
                      const v = m?.value ?? null;
                      return (
                        <td key={c} className="p-0.5">
                          <div className="num flex h-12 items-center justify-center rounded-sm" style={cellStyle(v)}>
                            {v == null ? "–" : Math.floor(v * 100 + 0.5)}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <ol className="space-y-6 lg:col-span-4">
          {FINDINGS.map(([lead, rest], i) => (
            <li key={lead} className="grid grid-cols-[2rem_1fr] gap-x-2">
              <span className="num text-step--1 text-muted" aria-hidden="true">
                {String(i + 1).padStart(2, "0")}
              </span>
              <p className="text-step-0 text-muted">
                <span className="font-medium text-ink">{lead}</span> {rest}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
