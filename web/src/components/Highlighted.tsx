/** The message with the hidden instruction marked; the mark carries a text label for screen readers. */
export function Highlighted({ message, hidden }: { message: string; hidden: string }) {
  const i = message.indexOf(hidden);
  if (!hidden || i < 0) return <>{message}</>;
  return (
    <>
      {message.slice(0, i)}
      <mark className="rounded-sm bg-danger-subtle px-0.5 text-danger underline decoration-danger decoration-1 underline-offset-4">
        <span className="sr-only">Hidden instruction: </span>
        {hidden}
      </mark>
      {message.slice(i + hidden.length)}
    </>
  );
}
