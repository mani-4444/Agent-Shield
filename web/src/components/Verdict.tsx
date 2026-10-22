import { CircleCheck, CircleX } from "lucide-react";

/** One defense's outcome: icon + words, never color alone. */
export function Verdict({ name, text, fooled }: { name: string; text: string; fooled: boolean }) {
  return (
    <div className="grid grid-cols-[1.25rem_1fr] gap-x-3 gap-y-0.5">
      {fooled ? (
        <CircleX className="mt-0.5 size-5 text-danger" aria-hidden="true" />
      ) : (
        <CircleCheck className="mt-0.5 size-5 text-success" aria-hidden="true" />
      )}
      <p className="text-step--1 font-medium text-ink">
        {name}
        <span className={`ml-2 font-normal ${fooled ? "text-danger" : "text-success"}`}>
          {fooled ? "fooled" : "held"}
        </span>
      </p>
      <p className="col-start-2 text-step--1 text-muted">{text}</p>
    </div>
  );
}
