import { EyeOff, MessageSquareText } from "lucide-react";
import type { Example } from "../types";
import { Highlighted } from "./Highlighted";

/** The test message as the assistant received it, drawn as an incoming chat bubble. */
export function PhoneMessage({ ex }: { ex: Example }) {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-line bg-bg p-4 sm:p-5">
      <div className="flex items-center gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-full bg-surface-2 text-muted" aria-hidden="true">
          <MessageSquareText className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-ink">Incoming message</p>
          <p className="truncate text-sm text-muted">
            Attacker’s goal: {ex.goal_name.toLowerCase()}
          </p>
        </div>
        <span className="num hidden text-sm text-muted sm:block">{ex.doc_id}</span>
      </div>

      <div className="mt-4 max-w-[34rem] rounded-2xl rounded-tl-md bg-surface-2 px-4 py-3">
        <p className="text-[0.9375rem] leading-relaxed break-words whitespace-pre-wrap text-ink" lang={ex.lang === "te" ? "te" : "en"}>
          <Highlighted message={ex.message} hidden={ex.hidden_instruction} />
        </p>
      </div>

      <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2 pt-4 text-sm">
        <span className="inline-flex items-center gap-2 text-muted">
          <span className="size-2.5 rounded-sm bg-danger" aria-hidden="true" />
          Hidden instruction
        </span>
        {ex.hidden_from_humans && (
          <span className="inline-flex items-center gap-1.5 text-danger">
            <EyeOff className="size-4" aria-hidden="true" />
            Invisible to people, read by the AI
          </span>
        )}
      </div>
    </div>
  );
}
