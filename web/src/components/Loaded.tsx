import type { ReactNode } from "react";
import type { LoadState } from "../useLoad";
import { StateMessage } from "./StateMessage";

export function Loaded<T>({ state, notFound, children }: { state: LoadState<T>; notFound?: ReactNode; children: (data: T) => ReactNode }) {
  switch (state.kind) {
    case "loading":
      return <StateMessage kind="loading" />;
    case "no-data":
      return <StateMessage kind="no-data" />;
    case "not-found":
      return <>{notFound ?? <StateMessage kind="not-found" />}</>;
    case "error":
      return <StateMessage kind="error" />;
    default:
      return <>{children(state.data)}</>;
  }
}
