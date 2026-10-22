import type { ReactNode } from "react";
import { Reveal } from "../motion";

export function SectionHeader({ id, eyebrow, title, lead }: { id: string; eyebrow: string; title: ReactNode; lead?: ReactNode }) {
  return (
    <Reveal className="mx-auto max-w-[44rem] text-center">
      <p className="eyebrow">{eyebrow}</p>
      <h2 id={id} className="mt-3 text-3xl text-ink">
        {title}
      </h2>
      {lead && <p className="mt-5 text-lg text-muted">{lead}</p>}
    </Reveal>
  );
}
