import { useEffect, useState } from "react";
import { NoDataYet, NotFound } from "./api";

export type LoadState<T> =
  | { kind: "loading" }
  | { kind: "ok"; data: T }
  | { kind: "no-data" }
  | { kind: "not-found" }
  | { kind: "error"; error: unknown };

export function useLoad<T>(load: () => Promise<T>, deps: unknown[] = []): LoadState<T> {
  const [state, setState] = useState<LoadState<T>>({ kind: "loading" });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const onRefresh = () => setTick((t) => t + 1);
    window.addEventListener("app:refresh", onRefresh);
    return () => window.removeEventListener("app:refresh", onRefresh);
  }, []);

  useEffect(() => {
    let alive = true;
    setState({ kind: "loading" });
    load().then(
      (data) => alive && setState({ kind: "ok", data }),
      (error) => {
        if (!alive) return;
        if (error instanceof NoDataYet) setState({ kind: "no-data" });
        else if (error instanceof NotFound) setState({ kind: "not-found" });
        else setState({ kind: "error", error });
      },
    );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return state;
}
