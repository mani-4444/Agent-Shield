import { CircleCheck, CircleX } from "lucide-react";

/** One defense's outcome as a row card: icon + word + what it did, never colour alone. */
export function Verdict({ name, text, fooled }: { name: string; text: string; fooled: boolean }) {
  return (
    <div
      className={`flex gap-3 rounded-xl border border-l-[3px] border-line bg-surface px-4 py-3 ${
        fooled ? "border-l-danger" : "border-l-success"
      }`}
    >
      {fooled ? (
        <CircleX className="mt-0.5 size-5 shrink-0 text-danger" aria-hidden="true" />
      ) : (
        <CircleCheck className="mt-0.5 size-5 shrink-0 text-success" aria-hidden="true" />
      )}
      <div className="min-w-0">
        <p className="text-[0.9375rem] font-medium text-ink">
          {name}
          <span className={`ml-2 text-sm font-semibold ${fooled ? "text-danger" : "text-success"}`}>
            {fooled ? "Fooled" : "Held"}
          </span>
        </p>
        <p className="mt-0.5 text-sm text-muted">{text}</p>
      </div>
    </div>
  );
}
