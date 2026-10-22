import { Megaphone, ShieldCheck, Tag, TriangleAlert, type LucideIcon } from "lucide-react";
import { CONFIG_ORDER, groupRows, headline, metric, results, shortName } from "../data";
import { Reveal, Stagger, StaggerItem } from "../motion";
import { SectionHeader } from "./SectionHeader";

const FAMILIES: [string, string][] = [
  ["F1_override", "Direct order to the AI"],
  ["F2_roleplay", "Fake system or admin message"],
  ["F3_hidden", "Text hidden from people"],
  ["F4_multilingual", "Telugu or mixed language"],
  ["F5_toolarg", "Fake tool call or corrected details"],
  ["F6_exfil", "Asks for the account number"],
];

const FINDINGS: [LucideIcon, string, string][] = [
  [ShieldCheck, "The fact-checker stops almost everything", "The AI never gets the power to pay or to see private details, so most tricks have nothing to grab."],
  [TriangleAlert, "Its weak spot: fake “corrected” details", "A believable new amount or payee can still pass the fact check now and then."],
  [Megaphone, "The detector hears loud tricks only", "It catches “ignore your rules”, but misses quiet ones like asking for the account number."],
  [Tag, "A warning label is not enough", "Telling the AI to ignore instructions inside the message helps only a little."],
];

/**
 * One hue (danger) laid over the cell colour at rising opacity; 50+ in 100 is the strongest step.
 * Capped at 60% so the printed number (always --text) stays readable in both themes.
 */
function cellStyle(v: number | null) {
  if (v == null) return {};
  const p = Math.round(Math.min(1, v / 0.5) * 60);
  const tint = `color-mix(in oklch, var(--danger) ${p}%, transparent)`;
  return { backgroundColor: "var(--surface-2)", backgroundImage: `linear-gradient(${tint}, ${tint})` };
}

export function Heatmap() {
  const rows = groupRows(results, "family");
  const names = Object.fromEntries(headline(results).map((r) => [r.config, r.name]));

  return (
    <section aria-labelledby="where-title" className="section border-y border-line bg-band">
      <div className="wrapper">
        <SectionHeader
          id="where-title"
          eyebrow="Where defenses fail"
          title="Which tricks get through which defense"
          lead="Attacks that worked, out of 100, for each kind of trick. The stronger the red, the more got through."
        />

        <div className="mt-14 grid gap-5">
          <Reveal className="card min-w-0 p-4 sm:p-6">
            <p className="mb-3 text-sm text-muted md:hidden">Scroll the table sideways to see all five defenses.</p>
            <div className="overflow-x-auto" tabIndex={0} role="region" aria-labelledby="where-title">
              <table className="w-full min-w-[40rem] table-fixed border-separate border-spacing-1.5 text-[0.9375rem]">
                <thead>
                  <tr>
                    <th scope="col" className="w-[26%] px-2 pb-2 text-left align-bottom font-medium text-muted">
                      Kind of trick
                    </th>
                    {CONFIG_ORDER.map((c) => (
                      <th
                        key={c}
                        scope="col"
                        className={`px-1 pb-2 text-center align-bottom font-medium ${c === "d" ? "text-accent" : "text-muted"}`}
                      >
                        {shortName(names[c] ?? c)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {FAMILIES.map(([fam, label]) => (
                    <tr key={fam}>
                      <th scope="row" className="px-2 text-left text-[0.9375rem] font-normal text-ink">
                        {label}
                      </th>
                      {CONFIG_ORDER.map((c) => {
                        const m = metric(rows.find((r) => r.config === c && r.group === `family=${fam}`), "asr_mean");
                        const v = m?.value ?? null;
                        return (
                          <td key={c} className="p-0">
                            <div
                              className="num flex h-14 items-center justify-center rounded-lg text-base font-semibold text-ink transition-shadow hover:ring-2 hover:ring-line-strong"
                              style={cellStyle(v)}
                            >
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
          </Reveal>

          <Stagger>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FINDINGS.map(([Icon, title, text]) => (
                <li key={title} className="flex">
                  <StaggerItem className="card card-hover flex w-full gap-4 p-5">
                  <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-surface-2 text-accent" aria-hidden="true">
                    <Icon className="size-[18px]" />
                  </span>
                  <div>
                    <p className="font-medium text-ink">{title}</p>
                    <p className="mt-1 text-sm text-muted">{text}</p>
                  </div>
                  </StaggerItem>
                </li>
            ))}
          </ul>
          </Stagger>
        </div>
      </div>
    </section>
  );
}
