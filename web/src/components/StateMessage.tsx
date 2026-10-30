const COPY = {
  loading: "Loading…",
  "no-data": "Collecting the first data from EA… check back in a few minutes.",
  error: "Couldn't load this right now. Try again in a moment.",
  "not-found": "Not found.",
} as const;

export function StateMessage({ kind, children }: { kind: keyof typeof COPY; children?: React.ReactNode }) {
  return (
    <div className={`state state-${kind}`} role={kind === "error" ? "alert" : "status"}>
      <p>{children ?? COPY[kind]}</p>
    </div>
  );
}
