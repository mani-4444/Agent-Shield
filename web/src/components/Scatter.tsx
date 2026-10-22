import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { metric, per100, shortName } from "../data";
import type { ConfigRow } from "../types";

const X_MAX = 0.35; // attacks that worked (share)
const Y_MIN = 0.6; // normal messages handled right (share)
const PAD = { top: 16, right: 20, bottom: 52, left: 52 };
const LABEL_GAP = 20;

function useWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.round(e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}

/**
 * Safety (x: attacks that worked, lower is better) against usefulness (y: normal messages
 * handled right). Drawn at the container's pixel width so text stays 14px on phones.
 * Crosshairs are the 95% ranges. A visually hidden table carries the same numbers.
 */
export function Scatter({ rows, highlight }: { rows: ConfigRow[]; highlight: string[] }) {
  const reduce = useReducedMotion();
  const [ref, width] = useWidth();
  const w = Math.max(width, 280);
  const h = Math.round(Math.min(440, Math.max(300, w * 0.66)));
  const iw = w - PAD.left - PAD.right;
  const ih = h - PAD.top - PAD.bottom;
  const x = (v: number) => PAD.left + (v / X_MAX) * iw;
  const y = (v: number) => PAD.top + (1 - (v - Y_MIN) / (1 - Y_MIN)) * ih;

  const points = rows.flatMap((r) => {
    const a = metric(r, "asr_mean");
    const b = metric(r, "benign_accuracy");
    if (a?.value == null || b?.value == null) return [];
    return [{ r, a, b, cx: x(a.value), cy: y(b.value), on: highlight.includes(r.config) }];
  });

  // Highlighted points: label to the right, past the CI line, nudged apart vertically if they
  // would overlap. Others: short name centred above or below, alternating left to right.
  const side = points
    .filter((p) => p.on)
    .map((p) => ({ key: p.r.config, x: Math.max(p.cx + 14, x(p.a.hi ?? 0) + 8), y: p.cy + 5, anchor: "start" as const }))
    .sort((m, n) => m.y - n.y);
  for (let i = 1; i < side.length; i++) if (side[i].y - side[i - 1].y < LABEL_GAP) side[i].y = side[i - 1].y + LABEL_GAP;
  const stacked = points
    .filter((p) => !p.on)
    .sort((m, n) => m.cx - n.cx)
    .map((p, i) => {
      const half = (shortName(p.r.name).length * 7.6) / 2;
      const cx = Math.min(Math.max(p.cx, PAD.left + half), w - PAD.right - half);
      return { key: p.r.config, x: cx, y: i % 2 === 0 ? p.cy - 14 : p.cy + 26, anchor: "middle" as const };
    });
  const labelAt = Object.fromEntries([...side, ...stacked].map((l) => [l.key, l]));
  const xTicks = [0, 0.1, 0.2, 0.3];
  const yTicks = [0.6, 0.7, 0.8, 0.9, 1];

  return (
    <div ref={ref}>
      {width > 0 && (
        <svg width={w} height={h} role="img" aria-label="Scatter chart of safety against usefulness for the five defenses" className="block overflow-visible">
          {/* better corner: few attacks, most normal messages right */}
          <rect x={x(0)} y={y(1)} width={x(0.1) - x(0)} height={y(0.9) - y(1)} rx={8} fill="var(--accent)" fillOpacity={0.12} />
          {x(0.1) - x(0) >= 130 && (
            <text x={x(0.1) - 10} y={y(0.9) - 10} textAnchor="end" fill="var(--accent)" fontSize={14} fontWeight={500}>
              Best corner
            </text>
          )}

          {xTicks.map((t) => (
            <g key={`x${t}`}>
              <line x1={x(t)} x2={x(t)} y1={PAD.top} y2={PAD.top + ih} stroke="var(--border)" />
              <text x={x(t)} y={PAD.top + ih + 22} textAnchor="middle" fill="var(--text-muted)" fontSize={14} className="num">
                {Math.round(t * 100)}
              </text>
            </g>
          ))}
          {yTicks.map((t) => (
            <g key={`y${t}`}>
              <line x1={PAD.left} x2={PAD.left + iw} y1={y(t)} y2={y(t)} stroke="var(--border)" />
              <text x={PAD.left - 10} y={y(t) + 5} textAnchor="end" fill="var(--text-muted)" fontSize={14} className="num">
                {Math.round(t * 100)}
              </text>
            </g>
          ))}
          <text x={PAD.left + iw / 2} y={h - 6} textAnchor="middle" fill="var(--text-muted)" fontSize={14}>
            Attacks that worked, per 100 → worse
          </text>
          <text
            transform={`translate(14 ${PAD.top + ih / 2}) rotate(-90)`}
            textAnchor="middle"
            fill="var(--text-muted)"
            fontSize={14}
          >
            Normal messages right, per 100
          </text>

          {points.map((p, i) => {
            const color = p.on ? "var(--accent)" : "var(--bar)";
            const l = labelAt[p.r.config];
            return (
              <motion.g
                key={p.r.config}
                initial={reduce ? false : { opacity: 0, scale: 0.6 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: reduce ? 0 : 0.08 * i }}
                style={{ transformOrigin: `${p.cx}px ${p.cy}px` }}
              >
                {p.a.lo != null && p.a.hi != null && (
                  <line x1={x(p.a.lo)} x2={x(p.a.hi)} y1={p.cy} y2={p.cy} stroke={color} strokeWidth={2} opacity={0.6} />
                )}
                {p.b.lo != null && p.b.hi != null && (
                  <line x1={p.cx} x2={p.cx} y1={y(p.b.lo)} y2={y(p.b.hi)} stroke={color} strokeWidth={2} opacity={0.6} />
                )}
                <circle cx={p.cx} cy={p.cy} r={7} fill={color} stroke="var(--surface)" strokeWidth={2} />
                <text
                  x={l.x}
                  y={l.y}
                  textAnchor={l.anchor}
                  fill={p.on ? "var(--text)" : "var(--text-muted)"}
                  fontSize={14}
                  fontWeight={p.on ? 600 : 500}
                  paintOrder="stroke"
                  stroke={p.on ? "none" : "var(--surface)"}
                  strokeWidth={5}
                  strokeLinejoin="round"
                >
                  {p.on ? p.r.name : shortName(p.r.name)}
                </text>
              </motion.g>
            );
          })}
        </svg>
      )}
      <div className="sr-only">
      <table>
        <caption>Safety against usefulness, per 100</caption>
        <thead>
          <tr>
            <th scope="col">Defense</th>
            <th scope="col">Attacks that worked</th>
            <th scope="col">Normal messages handled right</th>
          </tr>
        </thead>
        <tbody>
          {points.map((p) => (
            <tr key={p.r.config}>
              <th scope="row">{p.r.name}</th>
              <td>{per100(p.a.value)}</td>
              <td>{per100(p.b.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
