import { motion } from "framer-motion";
import { useRef, type KeyboardEvent, type ReactNode } from "react";

export interface Choice<T extends string> {
  value: T;
  label: ReactNode;
}

/**
 * A single-choice radio group drawn as a segmented control or a row of chips. One tab stop;
 * arrow keys, Home and End move the selection (WAI-ARIA radio group pattern). The selected
 * background slides between options via a shared layoutId.
 */
export function ChoiceGroup<T extends string>({
  id,
  label,
  options,
  value,
  onChange,
  variant = "segmented",
  className = "",
}: {
  id: string;
  label: string;
  options: Choice<T>[];
  value: T;
  onChange: (v: T) => void;
  variant?: "segmented" | "chips" | "list";
  className?: string;
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const active = Math.max(
    0,
    options.findIndex((o) => o.value === value),
  );

  function onKey(e: KeyboardEvent) {
    const n = options.length;
    const next =
      e.key === "ArrowRight" || e.key === "ArrowDown"
        ? (active + 1) % n
        : e.key === "ArrowLeft" || e.key === "ArrowUp"
          ? (active - 1 + n) % n
          : e.key === "Home"
            ? 0
            : e.key === "End"
              ? n - 1
              : null;
    if (next == null) return;
    e.preventDefault();
    onChange(options[next].value);
    refs.current[next]?.focus();
  }

  const group = {
    segmented: "inline-flex rounded-full bg-surface-2 p-1",
    chips: "flex flex-wrap gap-2",
    list: "flex flex-col gap-1",
  }[variant];
  const item = {
    segmented: "min-h-10 rounded-full px-4 text-sm font-medium",
    chips: "min-h-10 rounded-full border px-4 text-sm font-medium",
    list: "min-h-11 w-full rounded-xl px-3 text-left text-sm font-medium",
  }[variant];

  return (
    <div role="radiogroup" aria-label={label} onKeyDown={onKey} className={`${group} ${className}`}>
      {options.map((o, i) => {
        const on = i === active;
        const chipBorder = variant === "chips" ? (on ? "border-accent" : "border-line hover:border-line-strong") : "";
        return (
          <button
            key={o.value}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="radio"
            aria-checked={on}
            tabIndex={on ? 0 : -1}
            onClick={() => onChange(o.value)}
            className={`relative isolate transition-colors duration-150 ${item} ${chipBorder} ${
              on ? (variant === "chips" ? "text-accent" : "text-ink") : "text-muted hover:text-ink"
            }`}
          >
            {on && (
              <motion.span
                layoutId={`${id}-selected`}
                className={`absolute inset-0 -z-10 ${
                  variant === "segmented"
                    ? "rounded-full bg-surface shadow-sm ring-1 ring-line"
                    : variant === "chips"
                      ? "rounded-full bg-accent-subtle"
                      : "rounded-xl bg-accent-subtle"
                }`}
                transition={{ type: "spring", stiffness: 500, damping: 40 }}
              />
            )}
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
